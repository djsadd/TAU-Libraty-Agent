from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from .config import settings
from app.core.embeddings import embeddings
# Создаём клиента Qdrant
client = QdrantClient(url=settings.QDRANT_URL)

# Сплиттер для документов
splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)

# OpenAI embeddings

# Векторное хранилище
vectorstore = Qdrant(
    client=client,
    collection_name=settings.QDRANT_COLLECTION,
    embeddings=embeddings,
)


def ensure_collection_exists():
    # лениво создаём коллекцию вызовом .from_documents при первой загрузке
    pass


def index_documents(docs):
    # helper: чанкуем и индексируем
    splits = splitter.split_documents(docs)
    Qdrant.from_documents(
        documents=splits,
        embedding=embeddings,
        url=settings.QDRANT_URL,
        prefer_grpc=False,
        collection_name=settings.QDRANT_COLLECTION,
    )


def index_title(docs):
    splits = splitter.split_documents(docs)
    Qdrant.from_documents(
        documents=splits,
        embedding=embeddings,
        url=settings.QDRANT_URL,
        prefer_grpc=False,
        collection_name=settings.QDRANT_TITLE_COLLECTION,  # 👈 другая коллекция
    )


def get_title_retriever(k: int | None = None):
    title_vectorstore = Qdrant(
        client=client,
        collection_name=settings.QDRANT_TITLE_COLLECTION,
        embeddings=embeddings,
    )
    return title_vectorstore.as_retriever(search_kwargs={"k": k or settings.TOP_K})


def get_retriever(k: int | None = None):
    return vectorstore.as_retriever(search_kwargs={"k": k or settings.TOP_K})


def get_book_retriever():
    title_vectorstore = Qdrant(
        client=client,
        collection_name=settings.QDRANT_TITLE_COLLECTION,
        embeddings=embeddings,
    )
    return title_vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "score_threshold": 0.6,
            "k": 1000  # максимум
        }
    )

