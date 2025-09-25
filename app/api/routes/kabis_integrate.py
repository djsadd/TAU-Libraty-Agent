from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from kabisapi.main import get_token, api_get
from app.core.db import SessionLocal
from sqlalchemy import select, func
from app.models.kabis import Kabis
from kabisapi.read_kabis import parse_payload, flatten_copies
from app.core.config import settings

from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from typing import List, Dict

from app.core.db import SessionLocal
from app.models.job import Job, JobStatus
from app.models.books import Document
from ...worker import ingest_job  # импорт актёра
import uuid


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


router = APIRouter(prefix="/api", tags=["upload_kabis", "index_kabis_books"])


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
        stmt = select(Kabis).where(Kabis.is_indexed == False)
        rows = session.scalars(stmt).all()
        for row in rows:
            row_dict = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
            row_dict['title'] = row_dict["subjects"]
            print(row_dict)
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
