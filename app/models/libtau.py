# app/models/document.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, Float
from app.core.db import Base


class Library(Base):
    __tablename__ = "library"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String)
    pdf_id = Column(String)
    download_url = Column(String)
    file_is_indexed = Column(Boolean, default=False)
    title_is_indexed = Column(Boolean, default=False)
    timestamp = Column(Float, nullable=False)
