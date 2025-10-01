from langchain_groq import ChatGroq
from .config import settings

# создаётся один раз на импорт
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    groq_api_key=settings.GROQ_API_KEY,
    temperature=0.2,
    max_tokens=512,
)
