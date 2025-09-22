# app/models/document.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)              # название файла / книги
    file_path = Column(String, nullable=False)          # путь к файлу в хранилище
    file_type = Column(String, nullable=True)           # pdf | docx | txt | ...

    description = Column(Text, nullable=True)           # описание / метаданные
    owner = Column(String, nullable=True)               # кто загрузил

    is_enabled = Column(Boolean, default=True)          # можно ли использовать в поиске
    is_indexed = Column(Boolean, default=False)         # прошло ли индексирование

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
