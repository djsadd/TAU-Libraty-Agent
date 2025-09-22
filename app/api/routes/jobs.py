# app/api/routes/jobs.py
from fastapi import APIRouter, HTTPException
from app.core.db import SessionLocal
from app.models.job import Job

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    db = SessionLocal()
    job = db.get(Job, job_id)
    db.close()
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "id": job.id,
        "document_id": job.document_id,
        "status": job.status,
        "step": job.current_step,
        "progress": job.progress_pct,
        "error": job.error_message,
        "queued_at": job.queued_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }
