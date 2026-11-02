import logging
import time
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

_token_cache: dict = {}


async def get_twitch_token(client_id: str, client_secret: str) -> str:
    now = time.time()
    cached = _token_cache.get("token")
    if cached and cached["expires_at"] > now + 60:
        return cached["access_token"]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["token"] = {
        "access_token": data["access_token"],
        "expires_at": now + data.get("expires_in", 3600),
    }
    return data["access_token"]


def _headers(token: str, client_id: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Client-Id": client_id}


async def fetch_user_by_login(login: str, token: str, client_id: str) -> Optional[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/users",
            params={"login": login},
            headers=_headers(token, client_id),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
    return data[0] if data else None


async def fetch_clips_for_streamer(
    broadcaster_id: str,
    token: str,
    client_id: str,
    max_clips: int = 500,
) -> list[dict]:
    clips = []
    cursor = None
    async with httpx.AsyncClient() as client:
        while len(clips) < max_clips:
            params: dict = {"broadcaster_id": broadcaster_id, "first": 100}
            if cursor:
                params["after"] = cursor
            resp = await client.get(
                "https://api.twitch.tv/helix/clips",
                params=params,
                headers=_headers(token, client_id),
                timeout=20,
            )
            resp.raise_for_status()
            body = resp.json()
            page = body.get("data", [])
            clips.extend(page)
            cursor = body.get("pagination", {}).get("cursor")
            if not cursor or not page:
                break
    return clips[:max_clips]


async def fetch_clips_page(
    broadcaster_id: str,
    token: str,
    client_id: str,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> dict:
    params: dict = {"broadcaster_id": broadcaster_id, "first": limit}
    if cursor:
        params["after"] = cursor
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/clips",
            params=params,
            headers=_headers(token, client_id),
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
    return {
        "clips": body.get("data", []),
        "cursor": body.get("pagination", {}).get("cursor"),
    }


async def fetch_top_streams(
    token: str,
    client_id: str,
    language: str = "en",
    limit: int = 20,
) -> list[dict]:
    params: dict = {"first": limit}
    if language and language != "all":
        params["language"] = language
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/streams",
            params=params,
            headers=_headers(token, client_id),
            timeout=20,
        )
        resp.raise_for_status()
    return resp.json().get("data", [])


async def fetch_top_games(token: str, client_id: str, limit: int = 20) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/games/top",
            params={"first": limit},
            headers=_headers(token, client_id),
            timeout=20,
        )
        resp.raise_for_status()
    return resp.json().get("data", [])


async def fetch_category_clips(
    game_id: str,
    token: str,
    client_id: str,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> dict:
    params: dict = {"game_id": game_id, "first": limit}
    if cursor:
        params["after"] = cursor
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.twitch.tv/helix/clips",
            params=params,
            headers=_headers(token, client_id),
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
    return {
        "clips": body.get("data", []),
        "cursor": body.get("pagination", {}).get("cursor"),
    }
