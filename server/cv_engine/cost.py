"""Cost estimation for Anthropic API calls.

Prices are ballpark and will drift — verify against the current Anthropic pricing page
before trusting cost_pence for anything budget-critical. This module is intentionally
forgiving: unknown models return 0 rather than raising, because an unknown-model cost
miscalculation must never fail a pipeline run.
"""
from __future__ import annotations


# USD per million tokens. Source: Anthropic pricing as of spec date; verify on changes.
_MODEL_PRICING_USD_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0, "cache_read": 0.1},
    "claude-haiku-4-5":          {"input": 1.0, "output": 5.0, "cache_read": 0.1},
    "claude-sonnet-4-6":         {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-opus-4-7":           {"input": 15.0, "output": 75.0, "cache_read": 1.5},
}

# 1 USD ≈ 79 pence — coarse constant, drift is fine for a budget-tracking signal.
_USD_TO_PENCE = 79


def calculate_cost_pence(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
) -> int:
    if input_tokens < 0 or output_tokens < 0 or cache_read_tokens < 0:
        raise ValueError("Token counts must be non-negative")
    pricing = _MODEL_PRICING_USD_PER_MTOK.get(model)
    if pricing is None:
        return 0
    usd = (
        input_tokens * pricing["input"]
        + output_tokens * pricing["output"]
        + cache_read_tokens * pricing["cache_read"]
    ) / 1_000_000
    return round(usd * _USD_TO_PENCE)
