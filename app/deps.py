from fastapi import Depends
from .core.vectorstore import get_retriever
from .core.llm import llm

def get_llm():
    return llm

def get_retriever_dep():
    return get_retriever()
