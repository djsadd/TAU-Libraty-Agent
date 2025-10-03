from fastapi import APIRouter
from sqlalchemy import select
from app.models.kabis import Kabis

from app.core.book_quality_check import check_file
from app.core.db import SessionLocal
from app.models.job import Job, JobStatus
from app.models.books import Document
from ...worker import ingest_job
import uuid
import os
import requests
from pathlib import Path


router = APIRouter(prefix="/api", tags=["upload_kabis", "index_kabis_books", "index_kabis_file_books"])


@router.get("/index_kabis", summary="Индексирование библиотеки КАБИС",
             description="Индексирование библиотеки кабис")
async def kabis_index():
    with SessionLocal() as session:
        stmt = select(Kabis).where(Kabis.is_indexed==False)
        rows = session.scalars(stmt).all()
        for row in rows:
            row_dict = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
            document_id = str(uuid.uuid4())

            db = SessionLocal()

            # 3) создать Job в БД
            job = Job(document_id=document_id, status=JobStatus.queued)
            db.add(job)
            db.commit()
            db.refresh(job)
            db.close()

            # 4) поставить в очередь
            ingest_job.send(job.id, meta=row_dict)
            db.commit()
    return {"Hello": "World"}


@router.get("/index_kabis_file_books", summary="Индексирование библиотеки КАБИС",
             description="Индексирование библиотеки кабис")
async def index_kabis_file_books():
    path_url = "https://kabis.tau-edu.kz"   # лучше явно https://
    save_dir = Path("uploads")            # папка куда сохраняем файлы
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
            except requests.RequestException as e:
                print(f"⚠️ Ошибка скачивания {url}: {e}, пропускаем...")
                continue

            with open(save_path, "wb") as f:
                f.write(resp.content)

            print(f"✅ Saved {url} -> {save_path}")

            # проверка читаемости
            book_quality = check_file(save_path)
            if book_quality["verdict"] not in ("OK_TEXT", "OK_TEXT_PDF", "OK_OCR"):
                print(f"⚠️ Документ {filename} не читаемый, пропускаем...")
                continue

            document_id = str(uuid.uuid4())

            # создаём документ
            doc = Document(
                title=row.title or row.author,
                file_path=str(save_path),
                file_type=filename.split(".")[-1].lower(),
                kabis_id=row.id_book,
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
            ingest_job(job.id, str(filename), meta={"id_book": row.id_book, "title": row.title or row.author})

            # вот здесь обновляем поле у row (Kabis)
            row.file_is_index = True
            session.commit()

    return {"Hello": "World"}
