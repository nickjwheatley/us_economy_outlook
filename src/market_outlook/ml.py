from __future__ import annotations

from math import exp

from .models import BlockScore


COEFFICIENTS: dict[str, float] = {
    "Growth": -0.28,
    "Labor": -0.32,
    "Financial Conditions": -0.30,
    "Housing and Credit": -0.18,
    "Consumer and Business Health": -0.16,
    "Inflation": -0.10,
}

INTERCEPT = 6.00


def recession_probability(block_scores: list[BlockScore]) -> float:
    """Deterministic logistic prototype for 6-12 month recession probability."""
    score_by_block = {item.block: item.score for item in block_scores}
    logit = INTERCEPT
    for block, coefficient in COEFFICIENTS.items():
        logit += coefficient * score_by_block.get(block, 5.0)
    probability = 1.0 / (1.0 + exp(-logit))
    return round(probability, 3)


def ml_regime_score(probability: float) -> float:
    """Convert recession probability into a 1-10 regime score."""
    return round(max(1.0, min(10.0, 10.0 - probability * 8.0)), 2)
