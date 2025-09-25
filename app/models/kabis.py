# app/models/document.py
import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.db import Base


class Kabis(Base):
    __tablename__ = "kabis"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    position = Column(String, nullable=True) # pos
    id_book = Column(String, nullable=True) # idbk
    bbk_top = Column(String, nullable=True)
    bbk_tail = Column(String, nullable=True)
    bbk = Column(String, nullable=True)
    dept_code = Column(String, nullable=True)
    lang = Column(String, nullable=True)
    sigla = Column(String, nullable=True)
    author = Column(String, nullable=True)
    title = Column(String, nullable=True)
    pub_info = Column(String, nullable=True)
    year = Column(String, nullable=True)
    isbn = Column(String, nullable=True)
    subjects = Column(String, nullable=True)
    download_url = Column(String, nullable=True)
    open_url = Column(String, nullable=True)
    copy_location = Column(String, nullable=True)
    ab = Column(String, nullable=True)
    is_indexed = Column(Boolean, default=False)
    file_path = Column(String, nullable=True)          # путь к файлу в хранилище
    file_type = Column(String, nullable=True)           # pdf | docx | txt | ...
