from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.models.kabis import Kabis
import time
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ...deps import get_retriever_dep, get_llm, get_book_retriever_dep
from app.models.chat import ChatHistory
router = APIRouter(prefix="/api", tags=["chat", "chat_card"])
from app.core.db import SessionLocal
import re


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

    book_docs = book_retriever.invoke(req.query, config={"k": 10})
    id_books = [d.metadata.get("id_book") for d in book_docs if d.metadata]
    with SessionLocal() as session:
        kabis_records = session.query(Kabis).filter(Kabis.id_book.in_(id_books)).all()
        kb_map = [
            {
                "Language": k.lang,
                "title": k.author + " " + k.title,
                "pub_info": k.pub_info,
                "year": k.year,
                "subjects": k.subjects
            }
            for k in kabis_records
        ]

    book_cards = []
    for d in book_docs:
        m = d.metadata or {}
        book_cards.append({
            "source": "book_search",
            "title": m.get("title", "Неизвестная книга"),
            "author": m.get("author", ""),
            "page": m.get("page"),
            "id_book": m.get("id_book"),
            "text_snippet": (d.page_content or "")[:500].strip()
        })

    # Vector Search
    vec_docs = retriever.invoke(req.query, config={"k": req.k or 5})
    vector_cards = []
    for d in vec_docs:
        m = d.metadata or {}
        vector_cards.append({
            "source": "vector_search",
            "title": m.get("title", "Неизвестный источник"),
            "page": m.get("page"),
            "id_book": m.get("id_book"),
            "text_snippet": (d.page_content or "")[:600].strip()
        })

    annotated_cards = [] + kb_map
    for card in vector_cards:
        system_role = (
            "Ты — академический помощник. Кратко (1–2 предложения) объясни, "
            "почему этот источник может быть полезен студенту по данному вопросу."
        )
        human_msg = (
            f"Вопрос: {req.query}\n\n"
            f"Источник: {card['title']}\n\n"
            f"Фрагмент: {card['text_snippet']}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_role),
            ("human", human_msg)
        ])
        summary = llm.invoke(prompt.format_messages()).content
        annotated_cards.append({**card, "summary": summary})

    # --- Этап 5: Формирование финального ответа LLM ---
    context = "\n\n".join([
        f"[{d.metadata.get('title', '')}] {clean_context(d.page_content[:800])}"
        for d in vec_docs
    ])
    text_prompt = ChatPromptTemplate.from_messages([
        ("system", "Ты — интеллектуальный помощник университета Туран-Астана. Отвечай строго по контексту."),
        ("human", f"Вопрос студента: {req.query}\n\nКонтекст:\n{context}")
    ])
    final_answer = llm.invoke(text_prompt.format_messages()).content

    # --- Этап 6: Сохраняем историю ---
    save_chat_history(
        db=db,
        session_id=session_id,
        question=req.query,
        answer=final_answer,
        tools_used=["book_search", "vector_search"]
    )

    # --- Этап 7: Возвращаем результат ---
    return {
        "reply": "Найдено в следующих книгах:",
        "cards": annotated_cards  # объединённые карточки
    }


