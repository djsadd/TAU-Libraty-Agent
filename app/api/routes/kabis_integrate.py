from fastapi import APIRouter
from fastapi import BackgroundTasks
from sqlalchemy import select

from app.core.book_quality_check import check_file
from app.core.db import SessionLocal
from app.models.kabis import Kabis

from app.models.job import Job, JobStatus

from app.models.books import Document
from app.worker import ingest_job

import uuid
import os
import requests
from pathlib import Path


router = APIRouter(prefix="/api", tags=["index_kabis_books", "index_kabis_file_books"])


@router.get("/index_kabis",
            summary="Index titles from library information resources",
            description="Index titles from library information resources"
            )
async def kabis_index():
    with SessionLocal() as session:
        stmt = select(Kabis).where(Kabis.is_indexed==False)
        rows = session.scalars(stmt).all()
        for row in rows:
            row_dict = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
            document_id = str(uuid.uuid4())

            db = SessionLocal()

            job = Job(document_id=document_id, status=JobStatus.queued)
            db.add(job)
            db.commit()
            db.refresh(job)
            db.close()

            ingest_job.send(job.id, meta=row_dict)
            db.commit()
    return {"message": f"Index is stated", "queued_jobs": len(rows)}


@router.get("/index_kabis_file_books",
            summary="Индексирование KABIS",
            description="Запускает процесс индексирования файлов KABIS в фоне")
async def index_kabis_file_books(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_kabis_files)
    return {"status": "started", "message": "Индексирование запущено в фоне"}


def process_kabis_files():
    path_url = 'https://kabis.tau-edu.kz'
    save_dir = Path('uploads')
    save_dir.mkdir(exist_ok=True)

    with SessionLocal() as session:
        stmt = (
            select(Kabis)
            .where(
                Kabis.file_is_index.is_(False),
                Kabis.download_url.isnot(None)
            )
        )
        rows = session.scalars(stmt).all()

        for row in rows:
            url = f"{path_url}{row.download_url}"
            filename = os.path.basename(row.download_url)
            save_path = save_dir / filename

            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
            except requests.RequestException:
                continue

            with open(save_path, "wb") as f:
                f.write(resp.content)

            book_quality = check_file(save_path)
            if book_quality["verdict"] not in ("OK_TEXT", "OK_TEXT_PDF", "OK_OCR"):
                continue

            doc = Document(
                title=row.title or row.author,
                file_path=str(save_path),
                file_type=filename.split(".")[-1].lower(),
                id_book=row.id,
                source="kabis"
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)

            job = Job(
                document_id=doc.id,
                status=JobStatus.queued
            )

            session.add(job)
            session.commit()
            session.refresh(job)

            ingest_job(job.id, str(filename), meta={
                "id_book": row.id_book,
                "title_book": row.title or row.author,
                "doc_id": doc.id,
                "source_data": "kabis",
            })

            row.file_is_index = True
            session.commit()
