import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Clip, DownloadJob, Streamer
from backend.db.schemas import DownloadJobOut, EnqueueRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/queue", tags=["queue"])

_semaphore = asyncio.Semaphore(5)
_sse_queues: list[asyncio.Queue] = []


def _broadcast(event: dict):
    for q in _sse_queues:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


async def _run_job(job_id: int):
    from backend.db.database import SessionLocal
    from backend.services.downloader import download_clip

    async with _semaphore:
        db = SessionLocal()
        try:
            job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
            if not job:
                return
            job.status = "downloading"
            job.attempts += 1
            db.commit()
            _broadcast({"type": "job_update", "job": DownloadJobOut.model_validate(job).model_dump(mode="json")})

            clip = db.query(Clip).filter(Clip.id == job.clip_id).first()
            if not clip:
                job.status = "error"
                job.error_msg = "Clip not found"
                db.commit()
                return

            save_dir = Path(job.save_path or ".")
            if job.subfolder:
                save_dir = save_dir / job.subfolder
            elif clip.is_outro:
                save_dir = save_dir / "outro"
            save_dir.mkdir(parents=True, exist_ok=True)

            def _progress(pct: float):
                job.progress = pct
                db.commit()
                _broadcast({"type": "job_update", "job": DownloadJobOut.model_validate(job).model_dump(mode="json")})

            local_path = await download_clip(clip.twitch_clip_id, save_dir, _progress)
            job.local_path = str(local_path)
            job.status = "done"
            job.progress = 100.0
            clip.downloaded = True
            clip.local_path = str(local_path)
            db.commit()
            _broadcast({"type": "job_update", "job": DownloadJobOut.model_validate(job).model_dump(mode="json")})
        except Exception as exc:
            logger.error("Download job %s failed: %s", job_id, exc)
            try:
                job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
                if job:
                    job.status = "error"
                    job.error_msg = str(exc)
                    db.commit()
                    _broadcast({"type": "job_update", "job": DownloadJobOut.model_validate(job).model_dump(mode="json")})
            except Exception:
                pass
        finally:
            db.close()


@router.post("/enqueue", response_model=list[DownloadJobOut])
async def enqueue(body: EnqueueRequest, db: Session = Depends(get_db)):
    jobs = []
    for clip_id in body.clip_ids:
        clip = db.query(Clip).filter(Clip.id == clip_id).first()
        if not clip:
            continue
        if not body.overwrite:
            existing = db.query(DownloadJob).filter(
                DownloadJob.clip_id == clip_id,
                DownloadJob.status.in_(["pending", "downloading", "done"]),
            ).first()
            if existing:
                continue
        streamer = db.query(Streamer).filter(Streamer.id == clip.streamer_id).first()
        job = DownloadJob(
            clip_id=clip_id,
            clip_title=clip.title,
            streamer_name=streamer.display_name if streamer else None,
            status="pending",
            save_path=body.save_path,
            subfolder=body.subfolder,
        )
        db.add(job)
        db.flush()
        jobs.append(job)

    db.commit()
    for job in jobs:
        db.refresh(job)
        asyncio.create_task(_run_job(job.id))

    return jobs


@router.get("/stream")
async def stream_queue():
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _sse_queues.append(q)

    async def _gen() -> AsyncGenerator[str, None]:
        try:
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"ping\"}\n\n"
        finally:
            _sse_queues.remove(q)

    return StreamingResponse(_gen(), media_type="text/event-stream")


@router.get("", response_model=list[DownloadJobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(DownloadJob).order_by(DownloadJob.created_at.desc()).all()


@router.post("/{job_id}/retry", response_model=DownloadJobOut)
async def retry_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "pending"
    job.progress = 0.0
    job.error_msg = None
    db.commit()
    db.refresh(job)
    asyncio.create_task(_run_job(job.id))
    return job


@router.delete("/done", status_code=204)
def clear_done(db: Session = Depends(get_db)):
    db.query(DownloadJob).filter(DownloadJob.status == "done").delete()
    db.commit()


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete(job)
    db.commit()
