from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cv_engine.score.created_date import score_created_date


_NOW = datetime(2026, 4, 17, 12, 0, tzinfo=timezone.utc)


def test_null_created_scores_zero() -> None:
    assert score_created_date(None, now=_NOW) == 0


def test_under_30_days_scores_ten() -> None:
    assert score_created_date((_NOW - timedelta(days=1)).isoformat(), now=_NOW) == 10
    assert score_created_date((_NOW - timedelta(days=29)).isoformat(), now=_NOW) == 10


def test_30_to_90_days_scores_seven() -> None:
    assert score_created_date((_NOW - timedelta(days=30)).isoformat(), now=_NOW) == 7
    assert score_created_date((_NOW - timedelta(days=89)).isoformat(), now=_NOW) == 7


def test_90_to_180_days_scores_five() -> None:
    assert score_created_date((_NOW - timedelta(days=90)).isoformat(), now=_NOW) == 5
    assert score_created_date((_NOW - timedelta(days=179)).isoformat(), now=_NOW) == 5


def test_180_to_365_scores_three() -> None:
    assert score_created_date((_NOW - timedelta(days=180)).isoformat(), now=_NOW) == 3
    assert score_created_date((_NOW - timedelta(days=364)).isoformat(), now=_NOW) == 3


def test_over_365_scores_one() -> None:
    assert score_created_date((_NOW - timedelta(days=365)).isoformat(), now=_NOW) == 1
    assert score_created_date((_NOW - timedelta(days=2000)).isoformat(), now=_NOW) == 1


def test_future_date_is_treated_as_zero_days_old() -> None:
    """A CV 'created tomorrow' is still in the <30d warm window."""
    assert score_created_date((_NOW + timedelta(days=1)).isoformat(), now=_NOW) == 10


def test_naive_datetime_treated_as_utc() -> None:
    naive_iso = "2026-04-15T10:00:00"  # no timezone
    assert score_created_date(naive_iso, now=_NOW) == 10
