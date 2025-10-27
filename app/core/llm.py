# from langchain_groq import ChatGroq
# from .config import settings
#
# # создаётся один раз на импорт
# llm = ChatGroq(
#     model="openai/gpt-oss-120b",
#     groq_api_key=settings.GROQ_API_KEY,
#     temperature=0.0,
#     max_tokens=2048,
# )

from langchain_openai import ChatOpenAI
from .config import settings

# Создание клиента для OpenAI
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    openai_api_key=settings.OPENAI_SECRET_KEY,
    temperature=0.0,
    max_tokens=2048,
    streaming=True,  # ← ОБЯЗАТЕЛЬНО!
)