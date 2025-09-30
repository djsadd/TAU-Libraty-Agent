# worker.py
from datetime import datetime
from pathlib import Path

from celery import Celery
from app.core.db import SessionLocal
from app.core.loaders import load_docs, load_title_only
from app.core.vectorstore import index_documents
from app.models.job import Job, JobStatus
from app.models.kabis import Kabis
from app.core.config import settings

# === Celery init ===
celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=60 * 60,   # максимум 1 час
    result_expires=3600,       # хранить результаты 1 час
)


# === helpers ===
def update_job(db, job_id, **fields):
    job = db.get(Job, job_id)
    for k, v in fields.items():
        setattr(job, k, v)
    db.commit()


# === tasks ===
@celery_app.task(bind=True, max_retries=5, default_retry_delay=30, queue="default")
def ingest_job(self, job_id: str, filename: str | None = None, meta: dict | None = None):
    db = SessionLocal()
    try:
        update_job(db, job_id,
                   status=JobStatus.processing,
                   current_step="start",
                   progress_pct=1,
                   started_at=datetime.utcnow())

        # === extract ===
        update_job(db, job_id, current_step="extract", progress_pct=10)
        docs = load_docs(Path(settings.UPLOAD_DIR) / filename) if filename else load_title_only(meta)

        # === chunk ===
        update_job(db, job_id, current_step="chunk", progress_pct=40)
        index_documents(docs)

        # === embed ===
        update_job(db, job_id, current_step="embed", progress_pct=70)

        # === index ===
        update_job(db, job_id, current_step="index", progress_pct=90)
        if meta and meta.get("id_book"):
            book = db.query(Kabis).filter(Kabis.id_book == str(meta["id_book"])).first()
            if book:
                book.is_indexed = True
                db.commit()

        update_job(db, job_id,
                   status=JobStatus.succeeded,
                   current_step="done",
                   progress_pct=100,
                   finished_at=datetime.utcnow())
    except Exception as exc:
        update_job(db, job_id,
                   status=JobStatus.failed,
                   current_step="error",
                   error_message=str(exc),
                   finished_at=datetime.utcnow())
        raise self.retry(exc=exc)   # Celery retry
    finally:
        db.close()