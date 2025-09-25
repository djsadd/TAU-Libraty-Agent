# worker.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from datetime import datetime
from app.core.db import SessionLocal
from app.core.loaders import load_docs, load_title_only
from app.core.vectorstore import index_documents
from app.models.job import Job, JobStatus
from pathlib import Path
from .core.config import settings
from app.models.kabis import Kabis
# 1) подключаем Redis
broker = RedisBroker(host="localhost", port=6379, db=0)
dramatiq.set_broker(broker)


def update_job(db, job_id, **fields):
    job = db.get(Job, job_id)
    for k, v in fields.items():
        setattr(job, k, v)
    db.commit()


@dramatiq.actor(max_retries=5, min_backoff=30000)  # 30s, 2m, 10m...
def ingest_job(job_id: str, filename: str | None = None, meta: dict | None = None):
    if not filename:
        db = SessionLocal()
        try:
            update_job(db, job_id,
                       status=JobStatus.processing,
                       current_step="start",
                       progress_pct=1,
                       started_at=datetime.utcnow())

            # === extract ===
            update_job(db, job_id, current_step="extract", progress_pct=10)
            # ... твоя логика извлечения текста ...
            print(meta)
            docs = load_title_only(meta)
            # нормализация метаданных
            # for d in docs:
                # d.metadata.setdefault("source", str(meta))
                # d.metadata.setdefault("title", meta.stem)

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
        except Exception as e:
            update_job(db, job_id,
                       status=JobStatus.failed,
                       current_step="error",
                       error_message=str(e),
                       finished_at=datetime.utcnow())
        finally:
            db.close()
        return

    save_path = Path(settings.UPLOAD_DIR) / filename

    db = SessionLocal()
    try:
        update_job(db, job_id,
                   status=JobStatus.processing,
                   current_step="start",
                   progress_pct=1,
                   started_at=datetime.utcnow())

        # === extract ===
        update_job(db, job_id, current_step="extract", progress_pct=10)
        # ... твоя логика извлечения текста ...
        docs = load_docs(save_path)
        # нормализация метаданных

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
