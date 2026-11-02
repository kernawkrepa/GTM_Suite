import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.db.database import get_db
from backend.db.models import Clip, Streamer
from backend.db.schemas import (
    CheckLocalRequest, CheckLocalResult, ClipCountsOut, ClipOut, ClipUpdate
)

router = APIRouter(prefix="/clips", tags=["clips"])


def _approved_streamer_ids(db: Session) -> list[int]:
    rows = db.query(Streamer.id).filter(Streamer.contract_status == "approved").all()
    return [r.id for r in rows]


def _clip_to_out(clip: Clip) -> ClipOut:
    out = ClipOut.model_validate(clip)
    out.streamer_name = clip.streamer.display_name if clip.streamer else None
    out.streamer_login = clip.streamer.twitch_login if clip.streamer else None
    return out


@router.get("", response_model=list[ClipOut])
def list_clips(
    streamer_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    max_duration: Optional[float] = Query(None),
    favorites_only: bool = Query(False),
    short_clips_only: bool = Query(False),
    sort: str = Query("performance_score"),
    sort_dir: str = Query("desc"),
    db: Session = Depends(get_db),
):
    approved_ids = _approved_streamer_ids(db)
    q = (
        db.query(Clip)
        .options(joinedload(Clip.streamer))
        .filter(Clip.streamer_id.in_(approved_ids))
    )
    if streamer_id:
        q = q.filter(Clip.streamer_id == streamer_id)
    if date_from:
        q = q.filter(Clip.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(Clip.created_at <= datetime.fromisoformat(date_to))
    if max_duration:
        q = q.filter(Clip.duration <= max_duration)
    if favorites_only:
        q = q.filter(Clip.is_favorite == True)
    if short_clips_only:
        q = q.filter(Clip.duration <= 60)

    col = getattr(Clip, sort, Clip.performance_score)
    q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())
    return [_clip_to_out(c) for c in q.all()]


@router.get("/counts", response_model=ClipCountsOut)
def clip_counts(db: Session = Depends(get_db)):
    approved_ids = _approved_streamer_ids(db)
    base = db.query(Clip).filter(Clip.streamer_id.in_(approved_ids))
    return ClipCountsOut(
        total=base.count(),
        favorites=base.filter(Clip.is_favorite == True).count(),
        downloaded=base.filter(Clip.downloaded == True).count(),
        outro=base.filter(Clip.is_outro == True).count(),
    )


@router.post("/scan")
async def scan_clips(
    streamer_ids: Optional[list[int]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    from backend.config import get_settings
    from backend.services.clip_scanner import scan_streamer_clips

    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")

    if streamer_ids:
        streamers = db.query(Streamer).filter(Streamer.id.in_(streamer_ids)).all()
    else:
        streamers = db.query(Streamer).filter(Streamer.contract_status == "approved").all()

    async def _run():
        for streamer in streamers:
            await scan_streamer_clips(streamer.id)

    background_tasks.add_task(asyncio.create_task, _run())
    return {"message": f"Scan started for {len(streamers)} streamer(s)"}


@router.post("/check-local", response_model=list[CheckLocalResult])
def check_local(body: CheckLocalRequest):
    results = []
    base = Path(body.save_path)
    for item in body.items:
        found = None
        for ext in (".mp4", ".mkv", ".webm"):
            candidate = base / f"{item.streamer_login}_{item.twitch_clip_id}{ext}"
            if candidate.exists():
                found = str(candidate)
                break
        results.append(CheckLocalResult(clip_id=item.clip_id, exists=found is not None, path=found))
    return results


@router.patch("/{clip_id}", response_model=ClipOut)
def update_clip(clip_id: int, body: ClipUpdate, db: Session = Depends(get_db)):
    clip = (
        db.query(Clip)
        .options(joinedload(Clip.streamer))
        .filter(Clip.id == clip_id)
        .first()
    )
    if not clip:
        raise HTTPException(404, "Clip not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(clip, field, value)
    db.commit()
    db.refresh(clip)
    return _clip_to_out(clip)


@router.delete("/{clip_id}", status_code=204)
def delete_clip(clip_id: int, db: Session = Depends(get_db)):
    clip = db.query(Clip).filter(Clip.id == clip_id).first()
    if not clip:
        raise HTTPException(404, "Clip not found")
    db.delete(clip)
    db.commit()
