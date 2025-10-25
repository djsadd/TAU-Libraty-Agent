# app/models/document.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.sql import func
from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    kabis_id = Column(String, nullable=True)

    description = Column(Text, nullable=True)
    owner = Column(String, nullable=True)

    is_enabled = Column(Boolean, default=True)
    is_indexed = Column(Boolean, default=False)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    source = Column(String, nullable=True)
    id_book = Column(String, nullable=True)

