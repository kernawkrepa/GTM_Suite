import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


_BACKEND_ENV = Path(__file__).parent / ".env"


def _env_path() -> Path:
    data_dir = os.environ.get("GTM_DATA_DIR")
    if data_dir:
        return Path(data_dir) / ".env"
    return _BACKEND_ENV


def _env_files() -> list[str]:
    """Load backend/.env first, then userData/.env so the latter wins."""
    paths = [str(_BACKEND_ENV)]
    data_dir = os.environ.get("GTM_DATA_DIR")
    if data_dir:
        paths.append(str(Path(data_dir) / ".env"))
    return paths


class Settings(BaseSettings):
    TWITCH_CLIENT_ID: str = ""
    TWITCH_CLIENT_SECRET: str = ""
    DEFAULT_DOWNLOAD_PATH: str = ""
    HOME_DEFAULT_LANGUAGE: str = "en"
    DATABASE_URL: str = ""
    MAX_CONCURRENT_DOWNLOADS: int = 5
    SCAN_MAX_CLIPS_PER_STREAMER: int = 500

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


def save_settings(updates: dict) -> None:
    path = _env_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()

    existing.update({k: str(v) for k, v in updates.items() if v is not None})
    path.write_text(
        "\n".join(f"{k}={v}" for k, v in existing.items()) + "\n",
        encoding="utf-8",
    )
    reload_settings()
