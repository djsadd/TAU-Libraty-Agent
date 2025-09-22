# app/models/job.py
import uuid, enum
from sqlalchemy import Column, String, Integer, Enum, DateTime, Text
from sqlalchemy.sql import func
from app.core.db import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    succeeded = "succeeded"
    failed = "failed"
    canceled = "canceled"


class Job(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False)

    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.queued)
    current_step = Column(String, nullable=True)       # extract|chunk|embed|index
    progress_pct = Column(Integer, nullable=False, default=0)

    error_message = Column(Text, nullable=True)

    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
