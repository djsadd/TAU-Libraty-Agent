from fastapi import APIRouter
from fastapi.responses import JSONResponse
from kabisapi.main import get_token, api_get
from sqlalchemy import select, func
from app.models.kabis import Kabis
from kabisapi.read_kabis import parse_payload, flatten_copies
from app.core.config import settings
from app.core.db import SessionLocal

from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["index_kabis_books"])


def save_kabis_rows(session: Session, rows: list[dict]):
    for row in rows:
        idbk = (str(row.get("idbk")) or "").strip()
        if not idbk:
            continue
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


# kabis_service.py
def sync_kabis_upload():
    token = get_token(settings.KABIS_USERNAME, settings.KABIS_PASSWORD)
    books_count = api_get("/count_books", token).json()["Count book"][1]

    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(Kabis))
        row = count

        if row and row < books_count:
            json_kabis = api_get(
                "/get_books_range",
                token,
                params={"start_pos": int(row), "end_pos": int(books_count)}
            ).json()
            rows = parse_payload(json_kabis)
            rows_flat = flatten_copies(rows)
            save_kabis_rows(session, rows_flat)
            return json_kabis
        elif not row:
            json_kabis = api_get(
                "/get_books_range",
                token,
                params={"start_pos": 1, "end_pos": 100}
            ).json()
            rows = parse_payload(json_kabis)
            rows_flat = flatten_copies(rows)
            save_kabis_rows(session, rows_flat)
            return rows_flat
        return {"Count books": books_count}


@router.get("/upload_kabis")
async def kabis_upload():
    try:
        result = sync_kabis_upload()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse({"error": f"Internal error: {e}"}, status_code=500)