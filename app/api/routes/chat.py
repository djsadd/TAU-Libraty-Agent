from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.tools import tool

from ...deps import get_retriever_dep, get_llm, get_book_retriever_dep
router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    k: int | None = None


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
    print("\n\n".join(lines))
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
        subject = m.get("subject", "Дополнительная информация")

        lines.append(f"📘 {title}\nДоп. инфо: {subject}")
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


@router.post("/chat", summary="Чат с ИИ")
async def chat(req: ChatRequest,
               retriever=Depends(get_retriever_dep),          # фрагменты (контекст)
               book_retriever=Depends(get_book_retriever_dep),# книги (обзор)
               llm=Depends(get_llm)):

    try:
        # инструменты
        vs_tool = lambda q, k=5: vector_search.func(q, k, retriever=retriever)
        bs_tool = lambda q, k=30: book_search.func(q, k, retriever=book_retriever)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Ты помощник по поиску литературы в университете Туран-Астана. "
             "Используй предоставленный контекст и список книг для ответа на вопросы студентов. "
             "Если ответа нет — скажи об этом. Ответы возвращай в html формате"
             "Книги доступны только во внутренней библиотеке университета."),
            ("human", "Вопрос: {question}\n\nКонтекст:\n{context}\n\nКниги:\n{books}")
        ])

        chain = (
                RunnableParallel(
                    question=RunnablePassthrough(),
                    context=lambda x: vs_tool(x, req.k or 5),  # поиск фрагментов
                    books=lambda x: bs_tool(x, 30),  # поиск книг
                )
                | prompt
                | llm
        )

        answer = chain.invoke(req.query)
        return {"reply": answer.content}

    except Exception as e:
        return JSONResponse({"error": f"Internal error: {e}"}, status_code=500)
