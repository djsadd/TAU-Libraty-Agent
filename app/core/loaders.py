from pathlib import Path


def load_docs(path: str):
    p = Path(path)
    suffix = p.suffix.lower()

    print(p)
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
