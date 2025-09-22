from langchain_groq import ChatGroq
from .config import settings

# создаётся один раз на импорт
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0.2,
    max_tokens=512,
)
