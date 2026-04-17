"""Minimal retry helper for Anthropic calls.

The Anthropic SDK has its own retry, but we want to classify errors ourselves so the
pipeline can distinguish transient (retryable) from permanent (no-retry). Callers are
expected to raise TransientError or PermanentError from inside the wrapped function.
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class TransientError(Exception):
    """HTTP 429, 5xx, timeout, connection reset — retry with backoff."""


class PermanentError(Exception):
    """HTTP 400/401/403, schema-invalid response — do not retry."""


DEFAULT_DELAYS_SECONDS: tuple[float, ...] = (1.0, 5.0, 30.0)


def with_retry(fn: Callable[[], T], *, delays: tuple[float, ...] | list[float] = DEFAULT_DELAYS_SECONDS) -> T:
    """Call `fn`. On TransientError, sleep `delays[i]` and retry. Give up after all delays exhausted."""
    attempts = 0
    last_err: TransientError | None = None
    for delay in (0.0, *delays):
        if delay > 0:
            time.sleep(delay)
        try:
            return fn()
        except PermanentError:
            raise
        except TransientError as e:
            last_err = e
            attempts += 1
            continue
    assert last_err is not None
    raise last_err
