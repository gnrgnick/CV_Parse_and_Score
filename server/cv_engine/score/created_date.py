"""Created Date scorer — Python-deterministic, generous slow decay."""
from __future__ import annotations

from datetime import datetime, timezone


def score_created_date(created_at_iso: str | None, *, now: datetime) -> int:
    if created_at_iso is None:
        return 0

    created = datetime.fromisoformat(created_at_iso)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    days_old = max(0, (now - created).days)

    if days_old < 30:
        return 10
    if days_old < 90:
        return 7
    if days_old < 180:
        return 5
    if days_old < 365:
        return 3
    return 1
