from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from kabisapi.main import get_token, api_get
from app.core.db import SessionLocal
from sqlalchemy import select, func
from app.models.kabis import Kabis
from kabisapi.read_kabis import parse_payload, flatten_copies
from app.core.config import settings
from io import BytesIO

from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from typing import List, Dict
from app.core.book_quality_check import check_file
from app.core.db import SessionLocal
from app.models.job import Job, JobStatus
from app.models.books import Document
from app.worker import ingest_job
import uuid
import os
import requests
from pathlib import Path


def save_kabis_rows(session: Session, rows: list[dict]):
    for row in rows:
        idbk = (str(row.get("idbk")) or "").strip()
        if not idbk:
            continue

        # проверка на существование
        exists = session.scalar(select(Kabis.id_book).where(Kabis.id_book == idbk))
        if exists:
            continue
        session.add(Kabis(
            position=str(row.get("pos") or ""),
            id_book=idbk,
            bbk_top=row.get("bbk_top"),
            bbk_tail=row.get("bbk_tail"),
            bbk=row.get("bbk_top") or row.get("bbk_tail"),
            dept_code=row.get("dept_code"),
            lang=row.get("lang"),
            sigla=row.get("sigla"),
            author=row.get("author"),
            title=row.get("title"),
            pub_info=row.get("pub_info"),
            year=row.get("year"),
            isbn=row.get("isbn"),
            subjects=row.get("subjects"),
            download_url=row.get("download_url"),
            open_url=row.get("open_url"),
            copy_location=str(row.get("copy_location") or ""),
            ab=row.get("copy_count"),
        ))
        session.flush()
    session.commit()


router = APIRouter(prefix="/api", tags=["upload_kabis", "index_kabis_books", "index_kabis_file_books"])


@router.get("/upload_kabis", summary="Загрузка данных в Kabis",
             description="Загрузка книг из базы данных Кабис в библиотеку ИИ агента.")
async def kabis_upload():
    try:

        token = get_token(settings.KABIS_USERNAME, settings.KABIS_PASSWORD)
        books_count = api_get("/count_books", token).json()["Count book"][1]

        with SessionLocal() as session:
            count = session.scalar(
                select(func.count()).select_from(Kabis)
            )
            row = count
            if row:
                if row < books_count:
                    print(row, books_count)
                    json_kabis = api_get(
                        "/get_books_range",
                        token,
                        params={"start_pos": int(row), "end_pos": int(books_count)}
                    ).json()
                    rows = parse_payload(json_kabis)
                    rows_flat = flatten_copies(rows)
                    save_kabis_rows(session, rows_flat)
                    return json_kabis
                else:
                    return {"Count books": books_count}
            else:
                json_kabis = api_get(
                    "/get_books_range",
                    token,
                    params={"start_pos": 1, "end_pos": 100}
                ).json()
                print(json_kabis)
                rows = parse_payload(json_kabis)
                rows_flat = flatten_copies(rows)
                # save_kabis_rows(session, list(unique_rows.values()))
                save_kabis_rows(session, rows_flat)
                return rows_flat
            print("Row with max year:", row if row else None)

        return {"Count books": books_count}
    except Exception as e:
        return JSONResponse({"error": f"Internal error: {e}"}, status_code=500)


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
            ingest_job.delay(job.id, meta=row_dict)
            db.commit()
    return {"Hello": "World"}
@router.get("/index_kabis_file_books", summary="Индексирование библиотеки КАБИС",
             description="Индексирование библиотеки кабис")
async def index_kabis_file_books(batch_size: int = 10):
    path_url = "https://kabis.tau-edu.kz"
    save_dir = Path("uploads")
    save_dir.mkdir(exist_ok=True)

    file_paths = []

    with SessionLocal() as session:
        stmt = (
            select(Kabis)
            .where(
                Kabis.file_is_index.is_(False),
                Kabis.download_url.isnot(None)
            )
        )
        rows = session.scalars(stmt).all()

        batch_jobs = []

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
            file_paths.append(str(save_path))

            book_quality = check_file(save_path)
            if book_quality["verdict"] not in ("OK_TEXT", "OK_TEXT_PDF", "OK_OCR"):
                print(f"⚠️ Документ {filename} не читаемый, пропускаем...")
                continue

            document_id = str(uuid.uuid4())

            # Создаем Document
            doc = Document(
                title=row.title or row.author,
                file_path=str(save_path),
                file_type=filename.split(".")[-1].lower()
            )
            session.add(doc)

            # Сразу ставим file_is_index для Kabis
            row.file_is_index = True

            session.commit()
            session.refresh(doc)

            # Создаем Job
            job = Job(document_id=document_id, status=JobStatus.queued)
            session.add(job)
            session.commit()
            session.refresh(job)

            # Добавляем в батч для Celery
            batch_jobs.append({
                "job_id": job.id,
                "filename": str(save_path),
                "meta": None  # или сюда можно вставить meta=row_dict если нужно
            })

            # Отправляем батч, если набрали batch_size
            if len(batch_jobs) >= batch_size:
                from app.worker import ingest_job_batch
                ingest_job_batch.delay(batch_jobs)
                batch_jobs = []

        # Если остались jobs в конце списка, отправляем их
        if batch_jobs:
            from app.worker import ingest_job_batch
            ingest_job_batch.delay(batch_jobs)

    return {"total_files": len(file_paths), "status": "queued"}
