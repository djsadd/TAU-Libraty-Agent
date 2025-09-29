from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import Qdrant
from .config import settings
from .embeddings import embeddings

client = QdrantClient(url=settings.QDRANT_URL)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)

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


def get_retriever(k: int | None = None):
    return vectorstore.as_retriever(search_kwargs={"k": k or settings.TOP_K})


def get_book_retriever(k: int | None = None):
    return vectorstore.as_retriever(search_kwargs={"k": k or settings.TOP_K})
