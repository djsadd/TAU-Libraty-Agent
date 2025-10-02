from langchain_openai import OpenAIEmbeddings
from .config import settings


embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # или "text-embedding-3-large"
    api_key=settings.OPENAI_SECRET_KEY
)