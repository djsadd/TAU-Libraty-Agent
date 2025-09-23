from fastapi import APIRouter, UploadFile
from pathlib import Path
import uuid
from ...core.config import settings
from ...core.loaders import load_docs
from ...core.vectorstore import index_documents
from app.core.db import SessionLocal
from app.models.job import Job, JobStatus
from app.models.books import Document
from ...worker import ingest_job  # импорт актёра
from app.core.book_quality_check import check_file


router = APIRouter(prefix="/api", tags=["upload"])
files_db: dict[str, dict] = {}


@router.post("/upload", summary="Загрузить файл",
             description="Поддерживаются PDF, TXT, DOCX, EPUB. Файл сохраняется в папке `uploads`.")
async def upload(file: UploadFile):
    save_path = settings.UPLOAD_DIR / file.filename
    with open(save_path, "wb") as f:
        f.write(await file.read())
    book_quality = check_file(save_path)
    if book_quality["verdict"] in ("OK_TEXT", "OK_TEXT_PDF", "OK_OCR"):
        print("✅ Документ читаемый, можно индексировать")
    else:
        return {"status": "error, document not readable"}
    # 2) создать Document (если есть) -> здесь «document_id»
    document_id = str(uuid.uuid4())
    # 2) создаём документ
    db_doc = SessionLocal()

    doc = Document(
        title=file.filename,
        file_path=str(save_path),
        file_type=file.filename.split(".")[-1].lower(),
    )

    db_doc.add(doc)
    db_doc.commit()
    db_doc.refresh(doc)
    db = SessionLocal()

    # 3) создать Job в БД
    job = Job(document_id=document_id, status=JobStatus.queued)
    db.add(job)
    db.commit()
    db.refresh(job)
    db.close()

    # 4) поставить в очередь
    ingest_job.send(job.id, str(file.filename))
    doc.is_indexed = True
    db.commit()

    # Закрыть
    db_doc.refresh(doc)
    db_doc.close()
    db_doc.commit()
    # 5) ответить клиенту
    return {"document_id": document_id, "job_id": job.id, "status": "queued"}