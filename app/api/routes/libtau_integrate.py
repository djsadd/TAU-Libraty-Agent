from fastapi import APIRouter
import requests
from app.core.config import settings
from app.core.db import SessionLocal

from app.models.libtau import Library
from app.models.books import Document
from app.models.job import Job, JobStatus

from app.core.book_quality_check import check_file
from ...worker import ingest_job
import uuid
import time

from sqlalchemy import select

from pathlib import Path
import os

url = f"http://{settings.LIB_TAU_HOST}:{settings.LIB_TAU_PORT}/get_posts"
auth = (settings.LIB_TAU_USER, settings.LIB_TAU_PASSWORD)


router = APIRouter(prefix="/api", tags=["lib_tau_get_count_books", "index_library_file_books"])


@router.get("/lib_tau_get_count_books",
            summary="Количество книг базы lib.tau-edu.kz",
            description="Получение информации о количестве постов в БИЦ lib.tau-edu.kz")
async def lib_tau_get_count_books():
    response = requests.get(url, auth=auth)

    if response.status_code != 200:
        return {"error": f"lib.tau-edu.kz вернул {response.status_code}"}

    data = response.json()
    pdf_list = data.get("pdf_list", [])

    added = 0
    skipped = 0

    with SessionLocal() as session:
        for row in pdf_list:
            pdf_id = str(row.get("pdf_id"))
            title = row.get("post_title")
            pdf_url = row.get("pdf_url")

            # Проверяем, есть ли уже запись с таким pdf_id
            stmt = select(Library).where(Library.pdf_id == pdf_id)
            existing = session.execute(stmt).scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            # Добавляем новую запись
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


@router.get("/index_library_file_books", summary="Индексирование файлов Library",
             description="Индексирование файлов книг библиотечной базы Library")
async def index_library_file_books():
    save_dir = Path("uploads")            # папка куда сохраняем файлы
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
            url = f"{row.download_url}"
            filename = os.path.basename(row.download_url)
            save_path = save_dir / filename

            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as e:
                continue

            with open(save_path, "wb") as f:
                f.write(resp.content)

            # проверка читаемости
            book_quality = check_file(save_path)
            if book_quality["verdict"] not in ("OK_TEXT", "OK_TEXT_PDF", "OK_OCR"):
                continue

            document_id = str(uuid.uuid4())

            # создаём документ
            doc = Document(
                title=row.title,
                file_path=str(save_path),
                file_type=filename.split(".")[-1].lower(),
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)

            # создаём Job
            job = Job(document_id=document_id, status=JobStatus.queued)
            session.add(job)
            session.commit()
            session.refresh(job)

            # ставим в очередь
            ingest_job(job.id, str(filename), meta={"id": row.id, "title": row.title, "Library": True})

            # вот здесь обновляем поле у row (Kabis)
            row.file_is_indexed = True
            session.commit()

    return {"Hello": "World"}

