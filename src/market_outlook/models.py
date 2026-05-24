from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSeries:
    series_id: str
    source: str
    source_url: str
    block: str
    indicator_name: str
    frequency: str
    higher_is_better: bool
    leading_or_lagging: str
    value_unit: str
    change_unit: str
    notes: str


@dataclass(frozen=True)
class IndicatorSnapshot:
    series_id: str
    as_of: str
    value: float
    qoq_change: float
    yoy_change: float
    qoq_signal: float
    yoy_signal: float
    z_score: float
    momentum_3m: float
    momentum_6m: float
    momentum_12m: float
    threshold_distance: float
    freshness_days: int


@dataclass(frozen=True)
class IndicatorScore:
    series_id: str
    indicator_name: str
    block: str
    score: float
    contribution: float
    as_of: str
    value: float
    value_unit: str
    qoq_change: float
    yoy_change: float
    change_unit: str
    trajectory_score: float
    rationale: str


@dataclass(frozen=True)
class BlockScore:
    block: str
    score: float
    weight: float
    contribution: float


@dataclass(frozen=True)
class OutlookResult:
    headline_score: float
    rules_score: float
    ml_regime_score: float
    recession_probability: float
    regime: str
    recession_risk: str
    block_scores: list[BlockScore]
    indicator_scores: list[IndicatorScore]
    saas_implication: str
    vti_implication: str
