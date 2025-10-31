from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import re
from sqlalchemy import text

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
from app.core.config import settings
from sshtunnel import SSHTunnelForwarder
import mysql.connector

from pydantic import BaseModel
from typing import List, Optional
from ...deps import get_retriever_dep, get_llm, get_book_retriever_dep
from app.models.chat import ChatHistory
from app.core.db import SessionLocal
import re
from fastapi.responses import StreamingResponse
from app.models.books import Document
from sentence_transformers import CrossEncoder


router = APIRouter(prefix="/api", tags=["chat", "chat_card", "educational_discipline_list"])
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", device="cuda")


di_iin = {
    "021205551147": ["Криптографические методы защиты информации",
                     "Менеджмент",
                     "История Казахстана",
                     "Философия",
                     "Система управления базами данных",
                     "Компьютерные сети",
                     ]
}


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


async def summarize_card(llm, card):
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


@router.post("/chat_card", summary="Чат с карточками книг")
async def chat(req: ChatRequest,
               retriever=Depends(get_retriever_dep),
               book_retriever=Depends(get_book_retriever_dep),
               llm=Depends(get_llm),
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):

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

    # --- BOOK SEARCH ---
    book_docs = book_retriever.invoke(req.query, config={"k": 1000})
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

    # --- ВЕКТОРНЫЙ ПОИСК ---
    vec_docs = retriever.invoke(req.query, config={"k": 50})  # чуть больше кандидатов

    # --- РЕРАНКЕР: сортируем vec_docs по смысловой релевантности ---
    pairs = [(req.query, d.page_content or "") for d in vec_docs]
    scores = reranker.predict(pairs)

    for d, s in zip(vec_docs, scores):
        d.metadata["rerank_score"] = float(s)

    # Сортируем по убыванию
    vec_docs = sorted(vec_docs, key=lambda x: x.metadata.get("rerank_score", 0), reverse=True)

    # --- Собираем карточки ---
    vector_cards_dictionary = {}
    for d in vec_docs:
        m = d.metadata or {}
        id_book = m.get("id_book")
        text_snippet = (d.page_content or "")[:600].strip()
        page = m.get("page")

        if id_book not in vector_cards_dictionary:
            vector_cards_dictionary[id_book] = {
                "pages": [],
                "text_snippets": [],
            }

        vector_cards_dictionary[id_book]['pages'].append(page)
        vector_cards_dictionary[id_book]['text_snippets'].append(text_snippet)

    # --- Обогащаем метаданными из БД ---
    id_books = [d.metadata.get("doc_id") for d in vec_docs if d.metadata]
    with SessionLocal() as session:
        documents = session.query(Document).filter(Document.id.in_(id_books)).all()
        for doc in documents:
            if doc.source == 'kabis':
                record = session.query(Kabis).filter_by(id=doc.id_book).first()
                vector_cards_dictionary[doc.id_book].update({
                    "title": record.title or record.author,
                    "language": record.lang,
                    "pub_info": record.pub_info,
                    "subjects": record.subjects,
                    "download_url": "kabis.tau-edu.kz" + str(record.download_url)
                })
            elif doc.source == 'library':
                record = session.query(Library).filter_by(id=doc.id_book).first()
                vector_cards_dictionary[doc.id_book].update({
                    "title": record.title,
                    "download_url": record.download_url
                })

    # --- Асинхронное аннотирование ---
    tasks = [summarize_card(llm, card) for card in vector_cards_dictionary.items()]
    annotated_vector_cards = await asyncio.gather(*tasks)

    # --- Логируем ---
    save_chat_history(
        db=db,
        session_id=session_id,
        question=req.query,
        answer="",
        tools_used=["book_search", "vector_search", "reranker"]
    )

    return {
        "reply": "В библиотеке найдены следующие книги: ",
        "book_search": kb_map,
        "vector_search": annotated_vector_cards
    }


@router.get("/educational_discipline_list")
async def educational_program_list(
    current_user: User = Depends(get_current_user)
):
    return get_disciplines_from_platonus(current_user)


async def process_row(row, retriever, book_retriever, llm):
    # --- book search ---
    book_docs = book_retriever.invoke(row, config={"k": 5})
    id_books = [d.metadata.get("id_book") for d in book_docs if d.metadata]

    # --- синхронный блок с базой данных ---
    def fetch_kabis():
        with SessionLocal() as session:
            kabis_records = session.query(Kabis).filter(Kabis.id_book.in_(id_books)).all()
            return [
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

    kb_map = await asyncio.to_thread(fetch_kabis)

    # --- vector retrieval (без reranker) ---
    vec_docs = retriever.invoke(row, config={"k": 5})

    vector_cards_dictionary = {}
    for d in vec_docs:
        m = d.metadata or {}
        id_book = m.get("id_book")
        text_snippet = (d.page_content or "")[:600].strip()
        page = m.get("page")
        if id_book not in vector_cards_dictionary:
            vector_cards_dictionary[id_book] = {"pages": [], "text_snippets": []}
        vector_cards_dictionary[id_book]["pages"].append(page)
        vector_cards_dictionary[id_book]["text_snippets"].append(text_snippet)

    # --- enrich metadata from DB ---
    def enrich_from_db():
        id_books_local = [d.metadata.get("doc_id") for d in vec_docs if d.metadata]
        with SessionLocal() as session:
            documents = session.query(Document).filter(Document.id.in_(id_books_local)).all()
            for doc in documents:
                if doc.source == 'kabis':
                    record = session.query(Kabis).filter_by(id=doc.id_book).first()
                    if record:
                        vector_cards_dictionary[doc.id_book].update({
                            "title": record.title or record.author,
                            "language": record.lang,
                            "pub_info": record.pub_info,
                            "subjects": record.subjects,
                            "download_url": "kabis.tau-edu.kz" + str(record.download_url)
                        })
                elif doc.source == 'library':
                    record = session.query(Library).filter_by(id=doc.id_book).first()
                    if record:
                        vector_cards_dictionary[doc.id_book].update({
                            "title": record.title,
                            "download_url": record.download_url
                        })

    await asyncio.to_thread(enrich_from_db)

    # --- summarize ---
    tasks = [summarize_card(llm, card) for card in vector_cards_dictionary.items()]
    annotated_vector_cards = await asyncio.gather(*tasks)

    return {
        "reply": "В библиотеке найдены следующие книги: ",
        "book_search": kb_map,
        "vector_search": annotated_vector_cards
    }


@router.get("/chat_card_recommendations", summary="Рекомендации книг")
async def chat_card_recommendations(
               retriever=Depends(get_retriever_dep),
               book_retriever=Depends(get_book_retriever_dep),
               llm=Depends(get_llm),
               db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):

    user_iin = current_user.iin
    rows = di_iin[user_iin]

    tasks = [process_row(row, retriever, book_retriever, llm) for row in rows]
    results = await asyncio.gather(*tasks)

    cards = {row: result for row, result in zip(rows, results)}
    return cards


class LLMContextRequest(BaseModel):
    text_snippet: str
    title: str
    query: str
#


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


@router.get("/students/disciplines")
def get_disciplines_from_platonus(
        current_user: User = Depends(get_current_user)
):
    conn = mysql.connector.connect(
        host=settings.PLATONUS_DB_HOST,
        port=int(settings.PLATONUS_DB_PORT),
        user=settings.PLATONUS_DB_USER,
        password=settings.PLATONUS_DB_PASSWORD,
        database=settings.PLATONUS_DB_NAME
    )

    iin = current_user.iin

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT DATABASE(), VERSION();")
    print("Текущая база и версия:", cursor.fetchone())

    query = """
        SELECT 
            subjects.SubjectNameRU AS discipline
        FROM journal j
        JOIN students ON j.StudentID = students.StudentID
        JOIN studygroups ON j.StudyGroupID = studygroups.StudyGroupID
        JOIN subjects ON subjects.SubjectID = studygroups.subjectid
        WHERE j.markTypeID IN (2, 3, 4)
          AND year = 2025
          AND students.iinplt = %s
        GROUP BY discipline;
    """

    cursor.execute(query, (iin,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    disciplines = [row["discipline"] for row in results]

    return {"disciplines": disciplines}
