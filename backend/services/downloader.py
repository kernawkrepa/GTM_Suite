import asyncio
import logging
import re
import shutil
import sys
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

_PROGRESS_RE = re.compile(r"\[download\]\s+([\d.]+)%")


def _ytdlp_exe() -> str:
    venv_bin = Path(sys.executable).parent
    for name in ("yt-dlp", "yt-dlp.exe"):
        candidate = venv_bin / name
        if candidate.exists():
            return str(candidate)
    found = shutil.which("yt-dlp")
    if found:
        return found
    raise FileNotFoundError("yt-dlp not found; install it with: pip install yt-dlp>=2025.1.0")


async def download_clip(
    twitch_clip_id: str,
    save_dir: Path,
    progress_cb: Optional[Callable[[float], None]] = None,
) -> Path:
    url = f"https://www.twitch.tv/clip/{twitch_clip_id}"
    out_template = str(save_dir / f"%(uploader_id)s_%(id)s.%(ext)s")

    cmd = [
        _ytdlp_exe(),
        "--no-playlist",
        "--newline",
        "-o", out_template,
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    last_path: Optional[str] = None

    assert proc.stdout is not None
    async for raw_line in proc.stdout:
        line = raw_line.decode("utf-8", errors="replace").rstrip()
        logger.debug("yt-dlp: %s", line)

        m = _PROGRESS_RE.search(line)
        if m and progress_cb:
            progress_cb(float(m.group(1)))

        if "[download] Destination:" in line:
            last_path = line.split("Destination:", 1)[1].strip()
        elif line.startswith("[download]") and "has already been downloaded" in line:
            last_path = line.split("]", 1)[1].strip().split(" has")[0].strip()

    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp exited with code {proc.returncode}")

    if last_path:
        return Path(last_path)

    # fallback: find newest file in save_dir
    candidates = sorted(save_dir.glob(f"*{twitch_clip_id}*"), key=lambda p: p.stat().st_mtime)
    if candidates:
        return candidates[-1]
    raise RuntimeError(f"Could not locate downloaded file for {twitch_clip_id}")
