from __future__ import annotations

import pytest

from cv_engine.retry import PermanentError, TransientError, with_retry


def test_with_retry_succeeds_on_first_attempt() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        return 42
    assert with_retry(f, delays=[0, 0, 0]) == 42
    assert calls["n"] == 1


def test_with_retry_retries_on_transient() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TransientError("flaky")
        return 7
    assert with_retry(f, delays=[0, 0, 0]) == 7
    assert calls["n"] == 3


def test_with_retry_raises_after_exhausted() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        raise TransientError("always flaky")
    with pytest.raises(TransientError):
        with_retry(f, delays=[0, 0, 0])
    assert calls["n"] == 4  # initial + 3 retries


def test_with_retry_no_retry_on_permanent() -> None:
    calls = {"n": 0}
    def f() -> int:
        calls["n"] += 1
        raise PermanentError("400 bad request")
    with pytest.raises(PermanentError):
        with_retry(f, delays=[0, 0, 0])
    assert calls["n"] == 1
