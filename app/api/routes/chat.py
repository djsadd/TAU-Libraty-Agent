from fastapi import APIRouter, Depends
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from fastapi.responses import JSONResponse
from ...deps import get_retriever_dep, get_llm

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    k: int | None = None


def _format_docs(docs, per_chunk_chars=800, max_chunks=5):
    lines = []
    for d in docs[:max_chunks]:
        m = d.metadata or {}
        title = m.get("title", "книга")
        page = m.get("page", "?")
        text = (d.page_content or "")[:per_chunk_chars].strip()
        lines.append(f"[{title}, стр. {page}] {text}")
    return "\n\n".join(lines)


@router.post("/chat", summary="Чат с ИИ",
             description="Отправь вопрос в поле `query`, получи ответ на основе контекста книг.")
async def chat(req: ChatRequest,
               retriever=Depends(get_retriever_dep),
               llm=Depends(get_llm)):
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты помощник по поиску литературы. Отвечай строго по контексту. "
                       "Если ответа нет — так и скажи и не передавай литературу. В конце укажи источники «Стр. X, файл Y»."),
            ("human", "Вопрос: {question}\n\nКонтекст:\n{context}")
        ])

        chain = (
            RunnableParallel(
                context=retriever.with_config({"k": req.k}) | _format_docs,
                question=RunnablePassthrough()
            )
            | prompt
            | llm
        )
        answer = chain.invoke(req.query)
        return {"reply": answer.content}
    except Exception as e:
        return JSONResponse({"error": f"Internal error: {e}"}, status_code=500)
