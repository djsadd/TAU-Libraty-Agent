# worker.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from datetime import datetime
from app.core.db import SessionLocal
from app.core.loaders import load_docs
from app.core.vectorstore import index_documents
from app.models.job import Job, JobStatus

# 1) подключаем Redis
broker = RedisBroker(host="localhost", port=6379, db=0)
dramatiq.set_broker(broker)


def update_job(db, job_id, **fields):
    job = db.get(Job, job_id)
    for k, v in fields.items():
        setattr(job, k, v)
    db.commit()

from pathlib import Path
from .core.config import settings
@dramatiq.actor(max_retries=5, min_backoff=30000)  # 30s, 2m, 10m...
def ingest_job(job_id: str, filename: str):

    save_path = Path(settings.UPLOAD_DIR) / filename

    db = SessionLocal()
    print("START")
    try:
        update_job(db, job_id,
                   status=JobStatus.processing,
                   current_step="start",
                   progress_pct=1,
                   started_at=datetime.utcnow())

        # === extract ===
        print("EXTRACT")
        update_job(db, job_id, current_step="extract", progress_pct=10)
        # ... твоя логика извлечения текста ...
        print("Job extract")
        docs = load_docs(save_path)
        print("Compelete")
        # нормализация метаданных
        for d in docs:
            d.metadata.setdefault("source", str(save_path))
            d.metadata.setdefault("title", save_path.stem)

        # === chunk ===
        update_job(db, job_id, current_step="chunk", progress_pct=40)
        # ... чанкование ...
        index_documents(docs)

        # === embed ===
        update_job(db, job_id, current_step="embed", progress_pct=70)
        # ... эмбеддинги ...

        # === index ===
        update_job(db, job_id, current_step="index", progress_pct=90)
        # ... запись в Qdrant ...

        update_job(db, job_id,
                   status=JobStatus.succeeded,
                   current_step="done",
                   progress_pct=100,
                   finished_at=datetime.utcnow())
    except Exception as e:
        update_job(db, job_id,
                   status=JobStatus.failed,
                   current_step="error",
                   error_message=str(e),
                   finished_at=datetime.utcnow())
    finally:
        db.close()
