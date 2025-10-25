from fastapi import APIRouter
from fastapi import BackgroundTasks
from sqlalchemy import select
import requests

from app.core.config import settings
from app.core.db import SessionLocal

from app.models.libtau import Library
from app.models.books import Document
from app.models.job import Job, JobStatus

from app.core.book_quality_check import check_file
from app.worker import ingest_job

import uuid
import time
from pathlib import Path
import os

url = f"http://{settings.LIB_TAU_HOST}:{settings.LIB_TAU_PORT}/get_posts"
auth = (settings.LIB_TAU_USER, settings.LIB_TAU_PASSWORD)

router = APIRouter(prefix="/api", tags=["lib_tau_get_count_books", "index_library_file_books"])


@router.get("/lib_tau_get_count_books", summary="GET count books in db lib.tau-edu.kz")
async def lib_tau_get_count_books():
    response = requests.get(url, auth=auth)
    if response.status_code != 200:
        return {"error": f"lib.tau-edu.kz back {response.status_code}"}

    data = response.json()
    pdf_list = data.get("pdf_list", [])

    added = 0
    skipped = 0

    with SessionLocal() as session:
        for row in pdf_list:
            pdf_id = str(row.get("pdf_id"))
            title = row.get("post_title")
            pdf_url = row.get("pdf_url")

            stmt = select(Library).where(Library.pdf_id == pdf_id)
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            new_book = Library(
                title=title,
                pdf_id=pdf_id,
                download_url=pdf_url,
                file_is_indexed=False,
                title_is_indexed=False,
                timestamp=time.time()
            )
            session.add(new_book)
            added += 1

        session.commit()

    return {
        "total": len(pdf_list),
        "added": added,
        "skipped": skipped
    }


def process_library_row(row_id: int):
    with SessionLocal() as session:
        row = session.get(Library, row_id)
        if not row or row.file_is_indexed:
            return

        download_url = row.download_url
        filename = os.path.basename(download_url)
        save_path = Path("uploads") / filename

        try:
            resp = requests.get(download_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            return

        with open(save_path, "wb") as f:
            f.write(resp.content)

        book_quality = check_file(save_path)
        if book_quality["verdict"] not in ("OK_TEXT", "OK_TEXT_PDF", "OK_OCR"):
            return

        doc = Document(
            title=row.title,
            file_path=str(save_path),
            file_type=filename.split(".")[-1].lower(),
            id_book=row.id,
            source="library"
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        job = Job(document_id=str(uuid.uuid4()), status=JobStatus.queued)
        session.add(job)
        session.commit()

        ingest_job.send(
            job.id,
            str(filename),
            meta={
                "id_book": row.id,
                "title_book": row.title,
                "Library": True,
                "doc_id": doc.id,
                "source_data": "libtau"
            }
        )

        row.file_is_indexed = True
        session.commit()


@router.get("/index_library_file_books", summary="Index file books from Library information resource lib.tau-edu.kz")
async def index_library_file_books(background_tasks: BackgroundTasks):
    save_dir = Path("uploads")
    save_dir.mkdir(exist_ok=True)

    with SessionLocal() as session:
        stmt = (
            select(Library)
            .where(
                Library.file_is_indexed.is_(False),
                Library.download_url.isnot(None)
            )
        )
        rows = session.scalars(stmt).all()

    for row in rows:
        background_tasks.add_task(process_library_row, row.id)

    return {"queued": len(rows)}
