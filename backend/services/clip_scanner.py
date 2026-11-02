import asyncio
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)

BATCH_SIZE = 5
BATCH_PAUSE = 1.0


def _performance_score(view_count: int, duration_hours: float) -> float:
    if duration_hours <= 0 or view_count <= 0:
        return 0.0
    raw = math.log10(view_count / math.sqrt(duration_hours)) * 2
    return max(0.0, min(10.0, raw))


async def scan_streamer_clips(streamer_id: int) -> int:
    from backend.config import get_settings
    from backend.db.database import SessionLocal
    from backend.db.models import Clip, Streamer
    from backend.services.twitch_api import get_twitch_token, fetch_clips_for_streamer

    settings = get_settings()
    db = SessionLocal()
    try:
        streamer = db.query(Streamer).filter(Streamer.id == streamer_id).first()
        if not streamer:
            logger.warning("scan_streamer_clips: streamer %s not found", streamer_id)
            return 0

        token = await get_twitch_token(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)
        raw_clips = await fetch_clips_for_streamer(
            streamer.twitch_id,
            token,
            settings.TWITCH_CLIENT_ID,
            max_clips=settings.SCAN_MAX_CLIPS_PER_STREAMER,
        )

        added = 0
        for i, clip_data in enumerate(raw_clips):
            twitch_id = clip_data.get("id")
            if not twitch_id:
                continue

            existing = db.query(Clip).filter(Clip.twitch_clip_id == twitch_id).first()
            if existing:
                existing.view_count = clip_data.get("view_count", existing.view_count)
                existing.cached_at = datetime.utcnow()
                db.flush()
                continue

            duration_s = float(clip_data.get("duration", 0))
            created_raw = clip_data.get("created_at")
            created_at = None
            if created_raw:
                try:
                    created_at = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                except ValueError:
                    pass

            clip = Clip(
                twitch_clip_id=twitch_id,
                streamer_id=streamer_id,
                title=clip_data.get("title"),
                thumbnail_url=clip_data.get("thumbnail_url"),
                clip_url=clip_data.get("url"),
                creator_name=clip_data.get("creator_name"),
                view_count=clip_data.get("view_count", 0),
                duration=duration_s,
                created_at=created_at,
                performance_score=_performance_score(
                    clip_data.get("view_count", 0),
                    duration_s / 3600 if duration_s > 0 else 0,
                ),
                cached_at=datetime.utcnow(),
            )
            db.add(clip)
            db.flush()
            added += 1

            if (i + 1) % BATCH_SIZE == 0:
                db.commit()
                await asyncio.sleep(BATCH_PAUSE)

        db.commit()
        streamer.last_scanned_at = datetime.utcnow()
        db.commit()
        logger.info("Scanned %s: %d new clips", streamer.twitch_login, added)
        return added
    except Exception as exc:
        logger.error("scan_streamer_clips %s failed: %s", streamer_id, exc)
        db.rollback()
        raise
    finally:
        db.close()
