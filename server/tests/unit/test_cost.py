from __future__ import annotations

import pytest

from cv_engine.cost import calculate_cost_pence


def test_haiku_basic_cost() -> None:
    # 10_000 input tokens + 1_000 output for Haiku ≈ $0.010 + $0.005 = $0.015 ≈ 1 pence
    pence = calculate_cost_pence(
        model="claude-haiku-4-5-20251001",
        input_tokens=10_000, output_tokens=1_000, cache_read_tokens=0,
    )
    assert pence >= 1


def test_sonnet_with_cache_is_cheaper_than_without() -> None:
    without_cache = calculate_cost_pence(
        model="claude-sonnet-4-6",
        input_tokens=5_000, output_tokens=500, cache_read_tokens=0,
    )
    with_cache = calculate_cost_pence(
        model="claude-sonnet-4-6",
        input_tokens=500, output_tokens=500, cache_read_tokens=4_500,
    )
    assert with_cache < without_cache


def test_unknown_model_returns_zero_not_raises() -> None:
    # Keep the writer forgiving — cost tracking must never fail a pipeline run.
    assert calculate_cost_pence(
        model="some-future-model",
        input_tokens=1000, output_tokens=500, cache_read_tokens=0,
    ) == 0


def test_negative_tokens_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_cost_pence(
            model="claude-haiku-4-5-20251001",
            input_tokens=-1, output_tokens=0, cache_read_tokens=0,
        )
