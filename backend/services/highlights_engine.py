import math
from typing import Optional


def compute_performance_score(view_count: int, duration_seconds: float) -> float:
    if duration_seconds <= 0 or view_count <= 0:
        return 0.0
    duration_hours = duration_seconds / 3600
    raw = math.log10(view_count / math.sqrt(duration_hours)) * 2
    return round(max(0.0, min(10.0, raw)), 2)


def rank_clips(clips: list[dict], top_n: Optional[int] = None) -> list[dict]:
    ranked = sorted(clips, key=lambda c: c.get("performance_score", 0.0), reverse=True)
    return ranked[:top_n] if top_n else ranked
