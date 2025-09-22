# app/schemas/document.py
from pydantic import BaseModel
from typing import Optional
import datetime


class DocumentCreate(BaseModel):
    title: str
    file_path: str
    file_type: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None


class DocumentRead(BaseModel):
    id: str
    title: str
    file_path: str
    file_type: Optional[str]
    description: Optional[str]
    owner: Optional[str]
    is_enabled: bool
    is_indexed: bool
    uploaded_at: datetime.datetime
    updated_at: Optional[datetime.datetime]

    class Config:
        orm_mode = True
