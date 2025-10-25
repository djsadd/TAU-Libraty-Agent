from fastapi import APIRouter
from fastapi.responses import JSONResponse
from kabisapi.main import get_token, api_get
from sqlalchemy import select, func
from app.models.kabis import Kabis
from kabisapi.read_kabis import parse_payload, flatten_copies
from app.core.config import settings
from app.core.db import SessionLocal

from sqlalchemy.orm import Session

router = APIRouter(prefix="/api", tags=["upload_kabis"])


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
    """
    Синхронизация локальной базы Kabis с удалённым источником.
    Загружает только новые книги, если их количество увеличилось.
    """
    token = get_token(settings.KABIS_USERNAME, settings.KABIS_PASSWORD)

    # Получаем общее количество книг с KABIS API
    kabis_count_resp = api_get("/count_books", token).json()
    kabis_count = kabis_count_resp.get("Count book", [0, 0])[1]

    with SessionLocal() as session:
        # Считаем количество записей в локальной таблице
        local_count = session.scalar(select(func.count()).select_from(Kabis)) or 0

        # --- Если локальная и удалённая база совпадают ---
        if local_count == kabis_count:
            print(f"[INFO] Данные уже синхронизированы. Локально: {local_count}, KABIS: {kabis_count}")
            return {
                "status": "up_to_date",
                "message": "Данные уже синхронизированы.",
                "count": kabis_count,
            }

        # --- Если локальная база пуста (первая загрузка) ---
        if local_count == 0:
            print("[INFO] Первая загрузка данных с KABIS...")
            json_kabis = api_get(
                "/get_books_range",
                token,
                params={"start_pos": 1, "end_pos": kabis_count}
            ).json()

        # --- Если появились новые книги ---
        elif local_count < kabis_count:
            print(f"[INFO] Обнаружены новые книги: {kabis_count - local_count} шт.")
            json_kabis = api_get(
                "/get_books_range",
                token,
                params={"start_pos": int(local_count), "end_pos": int(kabis_count)}
            ).json()

        else:
            # Это на случай, если почему-то локальных книг больше (ошибка данных)
            print(f"[WARN] Локальных записей больше, чем в KABIS! ({local_count} > {kabis_count})")
            return {
                "status": "mismatch",
                "message": "Локальных записей больше, чем в KABIS.",
                "local_count": local_count,
                "kabis_count": kabis_count,
            }

        # --- Сохраняем новые данные ---
        rows = parse_payload(json_kabis)
        rows_flat = flatten_copies(rows)
        save_kabis_rows(session, rows_flat)

        print(f"[INFO] Успешно добавлено {len(rows_flat)} записей в базу.")
        return {
            "status": "success",
            "added": len(rows_flat),
            "new_total": kabis_count,
        }


@router.get("/upload_kabis", summary="Получение данных из базы Kabis")
async def kabis_upload():
    try:
        result = sync_kabis_upload()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse({"error": f"Internal error: {e}"}, status_code=500)