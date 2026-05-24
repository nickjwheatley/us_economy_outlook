from __future__ import annotations

from statistics import mean

from .ml import ml_regime_score, recession_probability
from .models import BlockScore, IndicatorScore, IndicatorSnapshot, OutlookResult, SourceSeries

BLOCK_WEIGHTS: dict[str, float] = {
    "Growth": 0.18,
    "Labor": 0.18,
    "Inflation": 0.13,
    "Financial Conditions": 0.14,
    "Consumer and Business Health": 0.09,
    "Housing and Credit": 0.10,
    "Fiscal and Policy": 0.04,
    "Market Valuation": 0.09,
    "Stress Signals": 0.05,
}


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def indicator_score(series: SourceSeries, snapshot: IndicatorSnapshot) -> float:
    directional_z = snapshot.z_score if series.higher_is_better else -snapshot.z_score
    trend = mean([snapshot.momentum_3m, snapshot.momentum_6m, snapshot.momentum_12m])
    directional_trend = trend if series.higher_is_better else -trend
    trajectory = mean([snapshot.qoq_signal, snapshot.yoy_signal])
    directional_trajectory = trajectory if series.higher_is_better else -trajectory
    freshness_penalty = clamp(snapshot.freshness_days / 120, 0, 0.35)

    normalized = (
        5.5
        + 1.20 * directional_z
        + 0.80 * directional_trend
        + 0.90 * directional_trajectory
        + 0.70 * snapshot.threshold_distance
        - freshness_penalty
    )
    return round(clamp(normalized, 1.0, 10.0), 2)


def trajectory_score(series: SourceSeries, snapshot: IndicatorSnapshot) -> float:
    trajectory = mean([snapshot.qoq_signal, snapshot.yoy_signal])
    return round(trajectory if series.higher_is_better else -trajectory, 2)


def rationale_for(score: float, series: SourceSeries, trajectory: float) -> str:
    if score >= 7:
        tone = "supportive"
    elif score >= 5:
        tone = "mixed"
    elif score >= 4:
        tone = "soft"
    else:
        tone = "stressed"
    if trajectory >= 0.25:
        direction = "and improving"
    elif trajectory <= -0.25:
        direction = "and deteriorating"
    else:
        direction = "with a flat trajectory"
    return f"{series.indicator_name} is {tone} for the {series.block.lower()} block {direction}."


def regime_for(score: float) -> str:
    if score < 2.5:
        return "depression-like or systemic crisis"
    if score < 4:
        return "recessionary"
    if score < 5:
        return "stall-speed slowdown"
    if score < 6.5:
        return "mixed or slowing expansion"
    if score < 8.5:
        return "healthy expansion"
    return "robust expansion"


def recession_risk_for(score: float) -> str:
    if score < 3:
        return "very high"
    if score < 4:
        return "high"
    if score < 5:
        return "elevated"
    if score < 6.5:
        return "moderate"
    return "low"


def saas_implication_for(score: float) -> str:
    if score < 4:
        return (
            "Severe SaaS deceleration risk. Expect pressure on new sales, net retention, "
            "seat expansion, churn, and management guidance."
        )
    if score < 5:
        return (
            "Elevated SaaS deceleration risk. Atlassian-like companies may still grow, "
            "but seat expansion, procurement cycles, billings, and net retention should be stress-tested."
        )
    if score < 6.5:
        return (
            "Mixed SaaS environment. Mission-critical platforms may remain resilient, "
            "while SMB, usage-based, and go-to-market software are more exposed."
        )
    return "Supportive SaaS environment, with better demand visibility and healthier expansion revenue."


def vti_implication_for(score: float, valuation_score: float | None = None) -> str:
    valuation_note = ""
    if valuation_score is not None:
        if valuation_score < 4:
            valuation_note = " Valuation is stretched, so forward-return expectations should be discounted."
        elif valuation_score < 5:
            valuation_note = " Valuation is somewhat expensive, leaving less margin for macro disappointment."
        elif valuation_score >= 7:
            valuation_note = " Valuation is supportive, improving the prospective risk/reward."

    if score < 4:
        return (
            "High equity drawdown and earnings-revision risk. VTI exposure should be evaluated "
            "against liquidity needs, diversification, valuation, and rebalancing policy."
            + valuation_note
        )
    if score < 5:
        return (
            "Fragile VTI backdrop. Drawdown and earnings-revision risk are elevated, "
            "but falling rates or contained credit spreads can partly offset weak growth."
            + valuation_note
        )
    if score < 6.5:
        return (
            "Mixed VTI backdrop. Market breadth, credit spreads, valuation, and earnings revisions should confirm the signal."
            + valuation_note
        )
    return (
        "Supportive VTI macro backdrop, though valuation and inflation can still dominate shorter-term returns."
        + valuation_note
    )


def compute_outlook(
    registry: dict[str, SourceSeries],
    snapshots: dict[str, IndicatorSnapshot],
) -> OutlookResult:
    indicator_scores: list[IndicatorScore] = []

    for series_id, snapshot in snapshots.items():
        if series_id not in registry:
            continue
        series = registry[series_id]
        score = indicator_score(series, snapshot)
        trajectory = trajectory_score(series, snapshot)
        indicator_scores.append(
            IndicatorScore(
                series_id=series_id,
                indicator_name=series.indicator_name,
                block=series.block,
                score=score,
                contribution=0.0,
                as_of=snapshot.as_of,
                value=snapshot.value,
                value_unit=series.value_unit,
                qoq_change=snapshot.qoq_change,
                yoy_change=snapshot.yoy_change,
                change_unit=series.change_unit,
                trajectory_score=trajectory,
                rationale=rationale_for(score, series, trajectory),
            )
        )

    by_block: dict[str, list[IndicatorScore]] = {}
    for item in indicator_scores:
        by_block.setdefault(item.block, []).append(item)

    block_scores: list[BlockScore] = []
    weighted_sum = 0.0
    used_weight = 0.0

    for block, weight in BLOCK_WEIGHTS.items():
        items = by_block.get(block, [])
        if not items:
            continue
        block_score = round(mean(item.score for item in items), 2)
        contribution = round(block_score * weight, 3)
        block_scores.append(BlockScore(block=block, score=block_score, weight=weight, contribution=contribution))
        weighted_sum += contribution
        used_weight += weight

    rules_score = round(weighted_sum / used_weight if used_weight else 0.0, 2)
    recession_probability_value = recession_probability(block_scores)
    ml_score = ml_regime_score(recession_probability_value)
    headline = round((0.75 * rules_score) + (0.25 * ml_score), 2)
    valuation_score = next((item.score for item in block_scores if item.block == "Market Valuation"), None)
    return OutlookResult(
        headline_score=headline,
        rules_score=rules_score,
        ml_regime_score=ml_score,
        recession_probability=recession_probability_value,
        regime=regime_for(headline),
        recession_risk=recession_risk_for(headline),
        block_scores=block_scores,
        indicator_scores=indicator_scores,
        saas_implication=saas_implication_for(headline),
        vti_implication=vti_implication_for(headline, valuation_score),
    )
