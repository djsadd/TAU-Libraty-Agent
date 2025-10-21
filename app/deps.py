from fastapi import Depends
from .core.vectorstore import get_retriever, get_book_retriever
from .core.llm import llm


def get_llm():
    return llm


def get_retriever_dep():
    return get_retriever()


def get_book_retriever_dep():
    # retriever по аннотациям / метаданным книг
    return get_book_retriever()
