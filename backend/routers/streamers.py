from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import Streamer
from backend.db.schemas import StreamerCreate, StreamerOut, StreamerUpdate, FromDiscoveryRequest
from backend.services.twitch_api import get_twitch_token, fetch_user_by_login

router = APIRouter(prefix="/streamers", tags=["streamers"])


@router.get("", response_model=list[StreamerOut])
def list_streamers(db: Session = Depends(get_db)):
    return db.query(Streamer).order_by(Streamer.display_name).all()


@router.post("", response_model=StreamerOut, status_code=201)
def create_streamer(body: StreamerCreate, db: Session = Depends(get_db)):
    existing = db.query(Streamer).filter(Streamer.twitch_id == body.twitch_id).first()
    if existing:
        raise HTTPException(409, "Streamer already exists")
    streamer = Streamer(**body.model_dump())
    db.add(streamer)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.post("/from-discovery", response_model=StreamerOut, status_code=201)
def add_from_discovery(body: FromDiscoveryRequest, db: Session = Depends(get_db)):
    existing = db.query(Streamer).filter(Streamer.twitch_id == body.user_id).first()
    if existing:
        raise HTTPException(409, "Streamer already exists")
    streamer = Streamer(
        twitch_id=body.user_id,
        twitch_login=body.user_login,
        display_name=body.display_name,
        avatar_url=body.avatar_url,
        contract_status="pending",
    )
    db.add(streamer)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.get("/{streamer_id}", response_model=StreamerOut)
def get_streamer(streamer_id: int, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(404, "Streamer not found")
    return streamer


@router.patch("/{streamer_id}", response_model=StreamerOut)
def update_streamer(streamer_id: int, body: StreamerUpdate, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(404, "Streamer not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(streamer, field, value)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.delete("/{streamer_id}", status_code=204)
def delete_streamer(streamer_id: int, db: Session = Depends(get_db)):
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(404, "Streamer not found")
    db.delete(streamer)
    db.commit()


@router.post("/{streamer_id}/refresh", response_model=StreamerOut)
async def refresh_streamer(streamer_id: int, db: Session = Depends(get_db)):
    from backend.config import get_settings
    streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
    if not streamer:
        raise HTTPException(404, "Streamer not found")
    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")
    token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    user_data = await fetch_user_by_login(streamer.twitch_login, token, settings.TWITCH_CLIENT_ID)
    if user_data:
        streamer.display_name = user_data.get("display_name", streamer.display_name)
        streamer.avatar_url = user_data.get("profile_image_url", streamer.avatar_url)
        streamer.followers_count = user_data.get("followers_count", streamer.followers_count)
    db.commit()
    db.refresh(streamer)
    return streamer


@router.post("/import-csv", response_model=list[StreamerOut], status_code=201)
async def import_streamers_csv(rows: list[dict], db: Session = Depends(get_db)):
    created = []
    for row in rows:
        if not row.get("twitch_login"):
            continue
        existing = db.query(Streamer).filter(Streamer.twitch_login == row["twitch_login"]).first()
        if existing:
            continue
        streamer = Streamer(
            twitch_id=row.get("twitch_id", ""),
            twitch_login=row["twitch_login"],
            display_name=row.get("display_name", row["twitch_login"]),
            contract_status=row.get("contract_status", "pending"),
            notes=row.get("notes"),
        )
        db.add(streamer)
        created.append(streamer)
    db.commit()
    for s in created:
        db.refresh(s)
    return created
