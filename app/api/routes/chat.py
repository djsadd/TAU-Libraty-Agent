from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.tools import tool
from sqlalchemy.orm import Session

import time
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ...deps import get_retriever_dep, get_llm, get_book_retriever_dep
from app.models.chat import ChatHistory
router = APIRouter(prefix="/api", tags=["chat"])
from app.core.db import SessionLocal


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

RATE_LIMIT_SECONDS = 30  # интервал между запросами


@router.post("/chat", summary="Чат с ИИ")
async def chat(req: ChatRequest,
               retriever=Depends(get_retriever_dep),
               book_retriever=Depends(get_book_retriever_dep),
               llm=Depends(get_llm),
               db: Session = Depends(get_db)):

    session_id = req.sessionId or "anonymous"

    # Выполняем LLM
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

    # Обновляем время последнего запроса
    _last_request_time[session_id] = now

    vs_tool = lambda q, k=5: (vs_tool_used.append("vector_search") or vector_search.func(q, k, retriever=retriever))
    bs_tool = lambda q, k=10: (bs_tool_used.append("book_search") or book_search.func(q, k, retriever=book_retriever))

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Ты — интеллектуальный помощник по поиску литературы для студентов университета «Туран-Астана»."
            "Отвечай только на основании информации, представленной в разделе «Контекст» и «Книги»."
            "Не используй внешние источники и не придумывай факты, если данных в контексте недостаточно."
            "Если в предоставленных данных нет точного ответа — честно сообщи: "
            "«В доступных источниках университета Туран-Астана информации нет.» "
            "Отвечай кратко, по существу, в формате HTML, сохраняя структуру и читаемость (например, <p>, <ul>, <li>, <b>)."
            "Не добавляй вступлений, выводов или информации, не основанной на контексте."
        ),
        (
            "human",
            "Вопрос студента: {question}\n\n"
            "Контекст:\n{context}\n\n"
            "Список доступных книг:\n{books}"
        )
    ])

    chain = (
        RunnableParallel(
            question=RunnablePassthrough(),
            context=lambda x: vs_tool(x, req.k or 5),
            books=lambda x: bs_tool(x, 10),
        )
        | prompt
        | llm
    )

    answer = chain.invoke(req.query)

    # Сохраняем в БД
    save_chat_history(
        db=db,
        session_id=session_id,
        question=req.query,
        answer=answer.content,
        tools_used=list(set(vs_tool_used + bs_tool_used))
    )

    return {"reply": answer.content}
