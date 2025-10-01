import numpy as np
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from .config import settings


class E5InstructEmbeddings(Embeddings):
    def __init__(self, st_model: SentenceTransformer, batch_size: int = 32, max_length: int = 512):
        self.st = st_model
        self.batch_size = batch_size
        self.max_length = max_length

    @staticmethod
    def _l2_normalize(arr: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
        return arr / norm

    def embed_documents(self, texts):
        passages = [f"Passage: {t}" for t in texts]
        vecs = self.st.encode(passages, batch_size=self.batch_size, normalize_embeddings=False, show_progress_bar=False)
        return self._l2_normalize(np.asarray(vecs)).tolist()

    def embed_query(self, text):
        q = f"Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: {text}"
        vec = self.st.encode([q], batch_size=1, normalize_embeddings=False, show_progress_bar=False)
        return self._l2_normalize(np.asarray(vec))[0].tolist()

# глобальные синглтоны для экономии времени/памяти
st_model = SentenceTransformer(settings.E5_MODEL_NAME, device=settings.E5_DEVICE)
embeddings = E5InstructEmbeddings(st_model=st_model, batch_size=32, max_length=512)