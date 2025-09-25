from pathlib import Path
from langchain.schema import Document


def load_docs(path: str):
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader
        docs = PyPDFLoader(str(p)).load()
    elif suffix in {".txt", ".md"}:
        from langchain_community.document_loaders import TextLoader
        docs = TextLoader(str(p), encoding="utf-8").load()
        for d in docs:
            d.metadata.setdefault("page", 1)
    elif suffix == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader
        docs = Docx2txtLoader(str(p)).load()
        for d in docs:
            d.metadata.setdefault("page", 1)
    elif suffix == ".epub":
        from langchain_community.document_loaders import UnstructuredEPubLoader
        docs = UnstructuredEPubLoader(str(p)).load()
        for i, d in enumerate(docs, 1):
            d.metadata.setdefault("page", i)
    else:
        raise ValueError(f"Неизвестный формат: {suffix}")

    for d in docs:
        d.metadata.setdefault("source", str(p))
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
        raise ValueError("В meta должен быть хотя бы 'title'")

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

    # добавляем все остальные поля, что передали
    for k, v in meta.items():
        metadata.setdefault(k, v)

    doc = Document(page_content=content, metadata=metadata)
    return [doc]

