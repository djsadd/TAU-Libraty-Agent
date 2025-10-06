from pathlib import Path
from langchain.schema import Document

from PyPDF2 import PdfReader
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredEPubLoader,
)
from typing import Optional


POPLER_PATH = r"C:\poppler-25.07.0\Library\bin"


def is_text_based_pdf(path: str) -> bool:
    """
    Проверяет, есть ли в PDF реальный текст, а не только сканы.
    Возвращает True, если найден хотя бы один непустой текстовый фрагмент.
    """
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                return True
        return False
    except Exception:
        # если PDF битый или PyPDF2 не смог распарсить — считаем сканом
        return False


def load_docs(path: str, meta: Optional[dict] = None):
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        if is_text_based_pdf(str(p)):
            docs = PyPDFLoader(str(p)).load()
        else:
            # OCR-стратегия для сканов с указанием poppler_path
            docs = UnstructuredPDFLoader(str(p), strategy="ocr").load()

    elif suffix in {".txt", ".md"}:
        docs = TextLoader(str(p), encoding="utf-8").load()
        for d in docs:
            d.metadata.setdefault("page", 1)

    elif suffix == ".docx":
        docs = Docx2txtLoader(str(p)).load()
        for d in docs:
            d.metadata.setdefault("page", 1)

    elif suffix == ".epub":
        docs = UnstructuredEPubLoader(str(p)).load()
        for i, d in enumerate(docs, 1):
            d.metadata.setdefault("page", i)

    else:
        raise ValueError(f"Неизвестный формат: {suffix}")

    # общие метаданные
    for d in docs:
        d.metadata.setdefault("source", str(p))
        if meta and "title" in meta and meta["title"]:
            d.metadata.setdefault("title", meta["title"])
        else:
            d.metadata.setdefault("title", p.stem)

    return docs


def load_title_only(meta: dict) -> list[Document]:
    """
    Создаёт список Document из словаря метаданных, если файла нет.
    Обязательные ключи: title (строка).
    Опциональные: author, id_book, year, lang, dept_code и т.п.
    """
    title = (meta.get("title") or "").strip()

    if not title:
        title = meta.get("author")

    author = (meta.get("author") or "").strip()
    content = f"{author}. {title}" if author else title

    # метаданные по умолчанию
    metadata = {
        "title": title,
        "author": author or None,
        "page": None,            # для консистентности с load_docs
        "file_type": "none",
        "source": None,
        "has_text": False,       # признак, что текста нет
    }

    print("META:", metadata)
    # добавляем все остальные поля, что передали
    for k, v in meta.items():
        metadata.setdefault(k, v)

    doc = Document(page_content=content, metadata=metadata)
    return [doc]
