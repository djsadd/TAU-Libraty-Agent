# from qdrant_client import QdrantClient
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_qdrant import Qdrant
# from .config import settings
# from .embeddings import embeddings
from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from .config import settings
from .embeddings import embeddings

client = QdrantClient(
    url=settings.QDRANT_URL,
    prefer_grpc=True,  # ⚡ Используем gRPC для быстрой загрузки
)

# Настраиваем сплиттер
splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE or 1000,
    chunk_overlap=settings.CHUNK_OVERLAP or 100
)

vectorstore = Qdrant(
    client=client,
    collection_name=settings.QDRANT_COLLECTION,
    embeddings=embeddings,
)


def index_documents(docs, batch_size: int = 64):
    """Чанкуем и добавляем документы в коллекцию Qdrant с батчингом и gRPC"""
    splits = splitter.split_documents(docs)
    print(f"📚 Документов после split: {len(splits)}")

    total = len(splits)
    for i in range(0, total, batch_size):
        batch = splits[i : i + batch_size]
        vectorstore.add_documents(batch)
        print(f"✅ Добавлено {min(i+batch_size, total)} / {total} документов")


def get_retriever(k: int | None = None):
    return vectorstore.as_retriever(search_kwargs={"k": k or settings.TOP_K})


def get_book_retriever(k: int | None = None):
    return vectorstore.as_retriever(search_kwargs={"k": k or settings.TOP_K})
