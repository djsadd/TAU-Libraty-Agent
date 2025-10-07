from sqlalchemy import Column, String, Text, Float, Integer, JSON
from app.core.db import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), index=True)  # UUID
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tools_used = Column(JSON, default=[])        # список инструментов
    timestamp = Column(Float, nullable=False)   # UNIX timestamp
