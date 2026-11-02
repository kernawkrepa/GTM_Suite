import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx

from backend.db.schemas import DiscoveredStreamerOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discovery", tags=["discovery"])

ALLOWED_THUMBNAIL_HOSTS = {
    "clips-media-assets2.twitch.tv",
    "static-cdn.jtvnw.net",
}


@router.get("/top-streamers")
async def top_streamers(
    language: str = Query("en"),
    limit: int = Query(20),
):
    from backend.config import get_settings
    from backend.services.twitch_api import get_twitch_token, fetch_top_streams
    from backend.db.database import SessionLocal
    from backend.db.models import Streamer, DiscoveredStreamer
    from datetime import datetime

    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")

    token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    streams = await fetch_top_streams(token, settings.TWITCH_CLIENT_ID, language=language, limit=limit)

    db = SessionLocal()
    try:
        existing_ids = {r.twitch_id for r in db.query(Streamer.twitch_id).all()}
        result = []
        for s in streams:
            already_added = s["user_id"] in existing_ids
            disc = db.query(DiscoveredStreamer).filter(DiscoveredStreamer.user_id == s["user_id"]).first()
            if not disc:
                disc = DiscoveredStreamer(
                    user_id=s["user_id"],
                    user_login=s.get("user_login"),
                    display_name=s.get("user_name"),
                    game_name=s.get("game_name"),
                    viewer_count=s.get("viewer_count"),
                    language=s.get("language"),
                    is_mature=s.get("is_mature"),
                    last_seen_live_at=datetime.utcnow(),
                )
                db.add(disc)
            else:
                disc.viewer_count = s.get("viewer_count")
                disc.last_seen_live_at = datetime.utcnow()
            db.flush()
            out = DiscoveredStreamerOut.model_validate(disc)
            out.already_added = already_added
            result.append(out.model_dump())
        db.commit()
        return result
    finally:
        db.close()


@router.get("/streamer-profile")
async def streamer_profile(login: str = Query(...)):
    from backend.config import get_settings
    from backend.services.twitch_api import get_twitch_token, fetch_user_by_login

    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")

    token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    user = await fetch_user_by_login(login, token, settings.TWITCH_CLIENT_ID)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/streamer-clips")
async def streamer_clips(
    broadcaster_id: str = Query(...),
    limit: int = Query(20),
    cursor: Optional[str] = Query(None),
):
    from backend.config import get_settings
    from backend.services.twitch_api import get_twitch_token, fetch_clips_page

    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")

    token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    return await fetch_clips_page(broadcaster_id, token, settings.TWITCH_CLIENT_ID, limit=limit, cursor=cursor)


@router.get("/top-games")
async def top_games(limit: int = Query(20)):
    from backend.config import get_settings
    from backend.services.twitch_api import get_twitch_token, fetch_top_games

    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")

    token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    return await fetch_top_games(token, settings.TWITCH_CLIENT_ID, limit=limit)


@router.get("/category-clips")
async def category_clips(
    game_id: str = Query(...),
    limit: int = Query(20),
    cursor: Optional[str] = Query(None),
):
    from backend.config import get_settings
    from backend.services.twitch_api import get_twitch_token, fetch_category_clips

    settings = get_settings()
    if not settings.TWITCH_CLIENT_ID:
        raise HTTPException(400, "Twitch credentials not configured")

    token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
    return await fetch_category_clips(game_id, token, settings.TWITCH_CLIENT_ID, limit=limit, cursor=cursor)


@router.get("/clip-thumbnail")
async def clip_thumbnail(url: str = Query(...)):
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_THUMBNAIL_HOSTS:
        raise HTTPException(403, "Disallowed thumbnail host")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
    return StreamingResponse(
        iter([resp.content]),
        media_type=resp.headers.get("content-type", "image/jpeg"),
    )
