from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import re
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
router = APIRouter(prefix="/api", tags=["chat", "chat_card"])
from app.core.db import SessionLocal
import re
from fastapi.responses import StreamingResponse
from app.models.books import Document

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
    system_role = (
        "Ты — академический помощник. Кратко объясни, "
        "почему этот источник может быть полезен студенту по данному вопросу."
        "Ответ давай в формате: стр. X - объяснение. По всем страницам переданные тебе."
    )
    human_msg = (
        f"Вопрос: {req.query}\n\n"
        f"Источник: {value['title']}\n\n"
        f"Фрагмент: {context}"
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_role),
        ("human", human_msg)
    ])
    response = await llm.ainvoke(prompt.format_messages())  # <-- async вызов
    return {
        'title': value["title"],
        'download_url': value['download_url'],
        "text_snippet": context,
        "summary": response.content
            }


@router.post("/chat_card", summary="Чат с карточками книг")
async def chat(req: ChatRequest,
               retriever=Depends(get_retriever_dep),
               book_retriever=Depends(get_book_retriever_dep),
               llm=Depends(get_llm),
               db: Session = Depends(get_db)):

    session_id = req.sessionId or "anonymous"

    now = time.time()
    last_time = _last_request_time.get(session_id, 0)
    if now - last_time < RATE_LIMIT_SECONDS:
        return JSONResponse(
            {"error": f"Слишком частые запросы. Попробуйте через {int(RATE_LIMIT_SECONDS - (now - last_time))} сек."},
            status_code=429
        )
    _last_request_time[session_id] = now

    # --- BOOK SEARCH ---
    book_docs = book_retriever.invoke(req.query, config={"k": 10})
    id_books = [d.metadata.get("id_book") for d in book_docs if d.metadata]
    with SessionLocal() as session:
        kabis_records = session.query(Kabis).filter(Kabis.id_book.in_(id_books)).all()
        kb_map = [
            {
                "Language": k.lang,
                "title": f"{k.author} {k.title}",
                "pub_info": k.pub_info,
                "year": k.year,
                "subjects": k.subjects,
                "source": "book_search"
            }
            for k in kabis_records
        ]

    # --- VECTOR SEARCH ---
    vec_docs = retriever.invoke(req.query, config={"k": req.k or 5})

    vector_cards_dictionary = {}

    for d in vec_docs:
        m = d.metadata or {}
        id_book = m.get("id_book")
        if id_book in vector_cards_dictionary:
            text_snippet = (d.page_content or "")[:600].strip()
            page = m.get("page")
            vector_cards_dictionary[id_book]['pages'].append(page)
            vector_cards_dictionary[id_book]['text_snippets'].append(text_snippet)
        else:
            text_snippet = (d.page_content or "")[:600].strip()
            page = m.get("page")
            vector_cards_dictionary[id_book] = {
                "pages": [page],
                "text_snippets": [text_snippet],
            }

    id_books = [d.metadata.get("doc_id") for d in vec_docs if d.metadata]
    with SessionLocal() as session:
        documents = session.query(Document).filter(Document.id.in_(id_books)).all()
        for doc in documents:
            print(doc.source, doc.source == "library")
            if doc.source == 'kabis':
                record = session.query(Kabis).filter_by(id=doc.id_book).first()

                vector_cards_dictionary[doc.id_book]["title"] = record.title or record.author
                vector_cards_dictionary[doc.id_book]["language"] = record.lang
                vector_cards_dictionary[doc.id_book]["pub_info"] = record.pub_info
                vector_cards_dictionary[doc.id_book]["subjects"] = record.subjects
                vector_cards_dictionary[doc.id_book]["download_url"] = record.download_url
            elif doc.source == 'library':
                record = session.query(Library).filter_by(id=doc.id_book).first()

                vector_cards_dictionary[doc.id_book]["title"] = record.title
                vector_cards_dictionary[doc.id_book]["download_url"] = record.download_url

    semaphore = asyncio.Semaphore(3)

    async def summarize_card_limited(llm, req, card):
        async with semaphore:
            return await summarize_card(llm, req, card)

    tasks = [summarize_card_limited(llm, req, card) for card in vector_cards_dictionary.items()]
    annotated_vector_cards = await asyncio.gather(*tasks)

    save_chat_history(
        db=db,
        session_id=session_id,
        question=req.query,
        answer="",
        tools_used=["book_search", "vector_search"]
    )

    return {
        "reply": "В библиотеке найдены следующие книги: ",
        "book_search": kb_map,
        "vector_search": annotated_vector_cards
    }


class LLMContextRequest(BaseModel):
    text_snippet: str
    title: str
    query: str
@router.post("/generate_llm_context")
async def generate_llm_context(request: LLMContextRequest):
    async def text_stream():
        system_role = (
            "Ты — академический помощник. Кратко объясни, "
            "почему этот источник может быть полезен студенту по данному вопросу. "
            "Ответ давай в формате: стр. X - объяснение. По всем страницам переданные тебе."
        )
        human_msg = (
            f"Вопрос: {request.query}\n\n"
            f"Источник: {request.title}\n\n"
            f"Фрагмент: {request.text_snippet}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_role),
            ("human", human_msg)
        ])

        llm = get_llm()

        # Реальный стриминг от LLM:
        async for chunk in llm.astream(prompt.format_messages()):
            if chunk.content:
                yield chunk.content

    return StreamingResponse(text_stream(), media_type="text/plain")
