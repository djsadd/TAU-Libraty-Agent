from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import re
from app.core.security import get_current_user
from app.models.user import User
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.models.kabis import Kabis
from app.models.libtau import Library
import time
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ...deps import get_retriever_dep, get_llm, get_book_retriever_dep
from app.models.chat import ChatHistory
from app.core.db import SessionLocal
import re
from fastapi.responses import StreamingResponse
from app.models.books import Document
from sentence_transformers import CrossEncoder


router = APIRouter(prefix="/api", tags=["chat", "chat_card"])
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")


def clean_context(text: str) -> str:
    """
    Удаляет разделы со списками литературы и внешними источниками
    (включая 'Список литературы', 'Рекомендуемая литература', 'References' и их варианты)
    из предоставленного контекста книги.
    """
    # Сначала нормализуем пробелы (чтобы 'литер атура' стало 'литература')
    normalized = re.sub(r'\s+', ' ', text)

    # Удаляем всё, что идёт после типичных заголовков списков литературы
    pattern = r'(?i)(список\s+рекомендованной\s+литературы|список\s+литературы|основная\s+литература|дополнительная\s+литература|литература|references)\b.*'
    cleaned = re.sub(pattern, '', normalized)

    return cleaned.strip()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ChatHistoryItem(BaseModel):
    sessionId: str
    question: str
    answer: str
    tools_used: Optional[List[str]] = []
    timestamp: Optional[float] = None  # UNIX timestamp


def save_chat_history(db: Session, session_id: str, question: str, answer: str, tools_used: list[str]):
    item = ChatHistory(
        session_id=session_id,
        question=question,
        answer=answer,
        tools_used=tools_used,
        timestamp=time.time()
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


class ChatRequest(BaseModel):
    query: str
    k: int | None = None
    sessionId: Optional[str] = None  # новое поле


def _format_docs(docs, per_chunk_chars=800, max_chunks=5):
    lines = []
    for d in docs[:max_chunks]:
        m = d.metadata or {}
        title = m.get("title", "книга")
        # author = m.get("author", "неизвестен")
        # subject = m.get("subject")
        page = m.get("page", "?")
        text = (d.page_content or "")[:per_chunk_chars].strip()
        lines.append(f"[{title}, стр. {page}] {text}")
        print(title, m.get("source"), text)
    return "\n\n".join(lines)


# ---- Инструмент: векторный поиск ----
@tool("vector_search", return_direct=False)
def vector_search(query: str, k: int = 5, retriever=None) -> str:
    """
    Поиск фрагментов текста в библиотеке по смысловому сходству.
    Возвращает релевантные куски текста с указанием книги, автора и страницы.
    """
    print("Векторный поиск")
    if retriever is None:
        return "Retriever не подключён"
    docs = retriever.invoke(query, config={"k": k})
    return _format_docs(docs)


def _format_books(docs, max_items=None):
    lines = []
    limit = max_items or len(docs)   # если None → берем все
    for d in docs[:limit]:
        m = d.metadata or {}
        title = m.get("title", "Неизвестная книга")
        # subject = m.get("subject", "Дополнительная информация")
        print(title, m.get("title"), m.get("id_book"))

        lines.append(f"📘 {title}\n")
    return "\n\n".join(lines)


@tool("book_search")
def book_search(query: str, k: int = 50, retriever=None) -> str:
    """
    Обзорный поиск по книгам (эмбеддинги).
    Возвращает список релевантных книг (много).
    """
    print("Обзорный поиск")
    if retriever is None:
        return "Retriever для книг не подключён"

    docs = retriever.invoke(query, config={"k": k})
    return _format_books(docs, max_items=k)


# глобальный словарь для хранения времени последнего запроса
# ключ: sessionId, значение: timestamp последнего запроса
_last_request_time: dict[str, float] = {}

RATE_LIMIT_SECONDS = 5  # интервал между запросами


@router.post("/chat", summary="Чат с ИИ")
async def chat(req: ChatRequest,
               retriever=Depends(get_retriever_dep),
               book_retriever=Depends(get_book_retriever_dep),
               llm=Depends(get_llm),
               db: Session = Depends(get_db)):

    session_id = req.sessionId or "anonymous"

    vs_tool_used = []
    bs_tool_used = []

    # Проверка лимита
    now = time.time()
    last_time = _last_request_time.get(session_id, 0)

    if now - last_time < RATE_LIMIT_SECONDS:
        return JSONResponse(
            {"error": f"Слишком частые запросы. Попробуйте через {int(RATE_LIMIT_SECONDS - (now - last_time))} сек."},
            status_code=429
        )

    _last_request_time[session_id] = now

    # tools
    vs_tool = lambda q, k=5: (vs_tool_used.append("vector_search") or vector_search.func(q, k, retriever=retriever))
    bs_tool = lambda q, k=100: (bs_tool_used.append("book_search") or book_search.func(q, k, retriever=book_retriever))

    # Общий системный промпт
    system_prompt = (
        "Ты — интеллектуальный помощник по поиску информации в книгах университета «Туран-Астана».\n"
        "Отвечай строго на основании текста из раздела «Контекст», где указаны книги и страницы.\n"
        "Каждый факт или вывод обязательно сопровождай ссылкой на источник в формате:\n"
        "«(<i>название книги</i>, стр. N)».\n"
        "Если информации нет — честно сообщай: "
        "«В доступных источниках университета Туран-Астана информации нет.»\n"
        "Форматируй ответ в HTML с использованием тегов (<p>, <ul>, <li>, <b>, <i>).\n"
        "Не выдумывай книги и страницы, используй только те, что указаны в разделе «Контекст»."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        (
            "human",
            "Вопрос студента: {question}\n\n"
            "Контекст (текстовые фрагменты с указанием книги и страницы):\n{context}"
        ),
    ])

    # --- 1️⃣ Первый запрос — через vector_search ---
    vector_chain = (
        RunnableParallel(
            question=RunnablePassthrough(),
            context=lambda q: clean_context(vs_tool(q, req.k or 5)),
        )
        | prompt
        | llm
    )
    vector_answer = vector_chain.invoke(req.query).content

    # --- 2️⃣ Второй запрос — через book_search ---
    book_chain = (
        RunnableParallel(
            question=RunnablePassthrough(),
            context=lambda q: bs_tool(q, req.k or 100),
        )
        | prompt
        | llm
    )
    book_answer = book_chain.invoke(req.query).content

    # --- 3️⃣ Объединяем ответы ---
    final_answer = (
        "<h3>Ответ по внутренним источникам (векторный поиск):</h3>\n"
        f"{vector_answer}\n"
        "<hr>"
        "<h3>Ответ по книгам библиотеки:</h3>\n"
        f"{book_answer}"
    )

    # --- 4️⃣ Сохраняем в БД ---
    save_chat_history(
        db=db,
        session_id=session_id,
        question=req.query,
        answer=final_answer,
        tools_used=list(set(vs_tool_used + bs_tool_used)),
    )

    return {"reply": final_answer}


async def summarize_card(llm, req, card):
    key, value = card
    context = ''
    cards = {

    }
    for i in range(len(value["pages"])):
        context += "стр." + str(value["pages"][i]) + "\n"
        context += "фрагмент" + value["text_snippets"][i] + "\n"
    return {
        'title': value["title"],
        'download_url': value['download_url'],
        "text_snippet": context,
            }

from fastapi import Depends
import asyncio
import time
from sqlalchemy.orm import Session

# ... ваши импорты

@router.post("/chat_card", summary="Чат с карточками книг")
async def chat(
    req: ChatRequest,
    retriever=Depends(get_retriever_dep),
    book_retriever=Depends(get_book_retriever_dep),
    llm=Depends(get_llm),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_id = req.sessionId or "anonymous"

    # --- защита от спама ---
    now = time.time()
    last_time = _last_request_time.get(session_id, 0)
    if now - last_time < RATE_LIMIT_SECONDS:
        return JSONResponse(
            {"error": f"Слишком частые запросы. Попробуйте через {int(RATE_LIMIT_SECONDS - (now - last_time))} сек."},
            status_code=429
        )
    _last_request_time[session_id] = now

    k_vec = req.k or 15

    # --- BOOK SEARCH (async) ---
    try:
        book_docs = await book_retriever.ainvoke(req.query, config={"k": 10})
    except AttributeError:
        # если .ainvoke нет — унесём sync в threadpool
        book_docs = await asyncio.to_thread(book_retriever.invoke, req.query, {"k": 10})

    id_books_from_book_search = [d.metadata.get("id_book") for d in book_docs if getattr(d, "metadata", None)]

    # --- Запрос Kabis (sync DB -> threadpool) ---
    def fetch_kabis_records(ids):
        with SessionLocal() as session:
            return session.query(Kabis).filter(Kabis.id_book.in_(ids)).all()

    kabis_records = await asyncio.to_thread(fetch_kabis_records, id_books_from_book_search)

    kb_map = [
        {
            "Language": k.lang,
            "title": f"{k.author} {k.title}".strip(),
            "pub_info": k.pub_info,
            "year": k.year,
            "subjects": k.subjects,
            "source": "book_search",
            "id_book": k.id_book,
            "download_url": (k.download_url or None),
        }
        for k in kabis_records
    ]

    # --- ВЕКТОРНЫЙ ПОИСК (async) ---
    try:
        vec_docs = await retriever.ainvoke(req.query, config={"k": k_vec})
    except AttributeError:
        vec_docs = await asyncio.to_thread(retriever.invoke, req.query, {"k": k_vec})

    # --- РЕРАНКЕР (sync -> threadpool) ---
    pairs = [(req.query, (d.page_content or "")) for d in vec_docs]
    # Вынесем predict в threadpool, чтобы не блокировать event loop
    scores = await asyncio.to_thread(reranker.predict, pairs)

    for d, s in zip(vec_docs, scores):
        # гарантируем, что metadata есть
        if not getattr(d, "metadata", None):
            d.metadata = {}
        d.metadata["rerank_score"] = float(s)

    vec_docs.sort(key=lambda x: x.metadata.get("rerank_score", 0.0), reverse=True)

    # --- Собираем карточки по id_book (единый ключ!) ---
    vector_cards_by_book: dict[str, dict] = {}
    for d in vec_docs:
        m = d.metadata or {}
        id_book = m.get("id_book")  # единый ключ по всему пайплайну
        if not id_book:
            continue
        text_snippet = (d.page_content or "").strip()[:600]
        page = m.get("page")

        bucket = vector_cards_by_book.setdefault(id_book, {"pages": [], "text_snippets": []})
        bucket["pages"].append(page)
        bucket["text_snippets"].append(text_snippet)

    # --- Обогащение метаданными (исправлена путаница с doc_id/id_book) ---
    # Берём все id_book, что накопили выше
    all_id_books = list(vector_cards_by_book.keys())

    def fetch_doc_meta(id_books: list[str]):
        with SessionLocal() as session:
            # Ищем документы по id_book и source
            docs = session.query(Document).filter(Document.id_book.in_(id_books)).all()

            # Чтобы не делать по два запроса всякий раз
            kabis_ids = [d.id_book for d in docs if d.source == "kabis"]
            lib_ids   = [d.id_book for d in docs if d.source == "library"]

            kabis_map = {}
            if kabis_ids:
                for rec in session.query(Kabis).filter(Kabis.id_book.in_(kabis_ids)).all():
                    kabis_map[rec.id_book] = rec

            lib_map = {}
            if lib_ids:
                for rec in session.query(Library).filter(Library.id_book.in_(lib_ids)).all():
                    lib_map[rec.id_book] = rec

            enriched = {}
            for d in docs:
                if d.source == "kabis" and d.id_book in kabis_map:
                    r = kabis_map[d.id_book]
                    enriched[d.id_book] = {
                        "title": (r.title or r.author),
                        "language": r.lang,
                        "pub_info": r.pub_info,
                        "subjects": r.subjects,
                        "download_url": (str(r.download_url) if r.download_url else None),
                        "source": "kabis",
                        "id_book": d.id_book,
                    }
                elif d.source == "library" and d.id_book in lib_map:
                    r = lib_map[d.id_book]
                    enriched[d.id_book] = {
                        "title": r.title,
                        "download_url": (r.download_url or None),
                        "source": "library",
                        "id_book": d.id_book,
                    }
            return enriched

    enriched_meta = await asyncio.to_thread(fetch_doc_meta, all_id_books)

    # Сливаем enrichment в карточки
    for id_book, meta in enriched_meta.items():
        vector_cards_by_book.setdefault(id_book, {})
        vector_cards_by_book[id_book].update(meta)

    # --- Асинхронное аннотирование карточек (у вас уже async) ---
    # Предпочтительно передавать чистые dict
    tasks = [summarize_card(llm, req, {"id_book": bid, **card}) for bid, card in vector_cards_by_book.items()]
    annotated_vector_cards = await asyncio.gather(*tasks)

    # --- Лог ---
    save_chat_history(
        db=db,
        session_id=session_id,
        question=req.query,
        answer="",
        tools_used=["book_search", "vector_search", "reranker"]
    )

    return {
        "reply": "В библиотеке найдены следующие книги:",
        "book_search": kb_map,
        "vector_search": annotated_vector_cards
    }


class LLMContextRequest(BaseModel):
    text_snippet: str
    title: str
    query: str


@router.post("/generate_llm_context")
async def generate_llm_context(payload: LLMContextRequest, current_user: User = Depends(get_current_user)):
    system_role = (
        "Ты — академический помощник. Твоя задача — кратко и понятно объяснить, "
        "почему данный источник может быть полезен студенту по его специальности. "
        "Учитывай переданные тебе данные о студенте (ФИО и специальность) и вопрос, который он изучает. "
        "Ответ давай в формате: стр. X — объяснение, где X — номер страницы. "
        "Поясняй, какую ценность несёт каждая страница именно для студента с данной специальностью."
    )

    human_msg = (
        f"Вопрос: {payload.query}\n\n"
        f"Источник: {payload.title}\n\n"
        f"Фрагмент: {payload.text_snippet}"
        f"Пользователь: {current_user.full_name}, Специальность пользователя: {current_user.educational_program}"
    )
    print(current_user.full_name)
    # Подготовка сообщений под ваш LLM/LC
    from langchain.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_role),
        ("human", human_msg),
    ])
    msgs = prompt.format_messages()

    llm = get_llm()  # ДОЛЖЕН поддерживать streaming=True

    async def gen():
        yield " \n"

        async for chunk in llm.astream(msgs):
            text = getattr(chunk, "content", None)
            if text:
                yield text
                await asyncio.sleep(0)

        yield "\n"

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",  # для nginx
        "Connection": "keep-alive",
    }
    return StreamingResponse(gen(), media_type="text/plain; charset=utf-8", headers=headers)