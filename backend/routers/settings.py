from fastapi import APIRouter
from backend.db.schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings_route():
    from backend.config import get_settings
    s = get_settings()
    return SettingsOut(
        TWITCH_CLIENT_ID=s.TWITCH_CLIENT_ID,
        TWITCH_CLIENT_SECRET=s.TWITCH_CLIENT_SECRET,
        DEFAULT_DOWNLOAD_PATH=s.DEFAULT_DOWNLOAD_PATH,
        HOME_DEFAULT_LANGUAGE=s.HOME_DEFAULT_LANGUAGE,
        MAX_CONCURRENT_DOWNLOADS=s.MAX_CONCURRENT_DOWNLOADS,
        SCAN_MAX_CLIPS_PER_STREAMER=s.SCAN_MAX_CLIPS_PER_STREAMER,
    )


@router.post("", response_model=SettingsOut)
def save_settings_route(body: SettingsUpdate):
    from backend.config import save_settings, get_settings
    updates = body.model_dump(exclude_none=True)
    save_settings(updates)
    s = get_settings()
    return SettingsOut(
        TWITCH_CLIENT_ID=s.TWITCH_CLIENT_ID,
        TWITCH_CLIENT_SECRET=s.TWITCH_CLIENT_SECRET,
        DEFAULT_DOWNLOAD_PATH=s.DEFAULT_DOWNLOAD_PATH,
        HOME_DEFAULT_LANGUAGE=s.HOME_DEFAULT_LANGUAGE,
        MAX_CONCURRENT_DOWNLOADS=s.MAX_CONCURRENT_DOWNLOADS,
        SCAN_MAX_CLIPS_PER_STREAMER=s.SCAN_MAX_CLIPS_PER_STREAMER,
    )
