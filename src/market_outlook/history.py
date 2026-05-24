from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from statistics import mean, pstdev

from .models import IndicatorSnapshot, OutlookResult, SourceSeries

HISTORICAL_BLOCK_WEIGHTS: dict[str, float] = {
    "Growth": 0.24,
    "Labor": 0.23,
    "Financial Conditions": 0.16,
    "Housing and Credit": 0.12,
    "Inflation": 0.10,
    "Consumer and Business Health": 0.08,
    "Fiscal and Policy": 0.03,
    "Market Valuation": 0.02,
}

RECESSION_PERIODS = [
    {"start": "2001-03-01", "end": "2001-11-01", "label": "Dot-com recession"},
    {"start": "2007-12-01", "end": "2009-06-01", "label": "Great Recession"},
    {"start": "2020-02-01", "end": "2020-04-01", "label": "COVID recession"},
]


def month_sequence(end_year: int, end_month: int, months: int) -> list[str]:
    start_index = end_year * 12 + end_month - months
    dates: list[str] = []
    for offset in range(months):
        month_index = start_index + offset + 1
        year = month_index // 12
        month = month_index % 12
        if month == 0:
            year -= 1
            month = 12
        dates.append(date(year, month, 1).isoformat())
    return dates


def _latest_month(snapshots: dict[str, IndicatorSnapshot]) -> tuple[int, int]:
    latest = max(snapshot.as_of for snapshot in snapshots.values())
    parsed = date.fromisoformat(latest)
    return parsed.year, parsed.month


def load_historical_indicator_points(path: str | Path) -> dict[str, list[dict[str, float | str]]]:
    points: dict[str, list[dict[str, float | str]]] = {}
    history_path = Path(path)
    if not history_path.exists():
        return points
    with history_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = row.get("value", "").strip()
            if not value or value == ".":
                continue
            try:
                numeric_value = float(value)
            except ValueError:
                continue
            points.setdefault(row["series_id"], []).append(
                {
                    "date": row["date"],
                    "value": round(numeric_value, 4),
                    "source": row.get("source") or "Historical source data",
                }
            )
    return points


def generate_dashboard_history(
    registry: dict[str, SourceSeries],
    snapshots: dict[str, IndicatorSnapshot],
    result: OutlookResult,
    historical_points: dict[str, list[dict[str, float | str]]] | None = None,
    months: int = 360,
) -> dict[str, object]:
    end_year, end_month = _latest_month(snapshots)
    dates = month_sequence(end_year, end_month, months)
    historical_points = historical_points or {}

    indicators: dict[str, object] = {}
    for series_id, snapshot in snapshots.items():
        series = registry.get(series_id)
        if series is None:
            continue
        real_points = [
            point
            for point in historical_points.get(series_id, [])
            if dates[0] <= str(point["date"]) <= dates[-1]
        ]
        has_full_enough_span = bool(real_points) and str(real_points[0]["date"]) <= dates[24]
        if has_full_enough_span:
            indicators[series_id] = {
                "name": series.indicator_name,
                "block": series.block,
                "unit": series.value_unit,
                "higherIsBetter": series.higher_is_better,
                "historySource": str(real_points[0].get("source", "Historical source data")),
                "points": real_points,
            }

    score_points = _score_from_indicator_history(registry, indicators, result.headline_score)

    return {
        "score": score_points,
        "indicators": indicators,
        "recessions": RECESSION_PERIODS,
    }


def _score_from_indicator_history(
    registry: dict[str, SourceSeries],
    indicators: dict[str, object],
    current_score: float,
) -> list[dict[str, float | str]]:
    by_date_block: dict[str, dict[str, list[float]]] = {}
    breadth_by_date: dict[str, list[float]] = {}
    for series_id, payload in indicators.items():
        points = payload["points"]
        if len(points) < 24:
            continue
        values = [float(point["value"]) for point in points]
        center = mean(values)
        spread = pstdev(values) or 1.0
        if spread == 0:
            continue
        series = registry[series_id]
        for index, point in enumerate(points):
            level_z = (float(point["value"]) - center) / spread
            oriented_level = level_z if series.higher_is_better else -level_z
            lookback_index = max(0, index - 12)
            prior_value = float(points[lookback_index]["value"])
            momentum = 0.0 if prior_value == 0 else (float(point["value"]) - prior_value) / abs(prior_value)
            oriented_momentum = momentum if series.higher_is_better else -momentum
            indicator_score = 5.5 + 1.15 * oriented_level + 7.0 * oriented_momentum
            indicator_score = max(1.0, min(10.0, indicator_score))
            by_date_block.setdefault(str(point["date"]), {}).setdefault(series.block, []).append(indicator_score)
            breadth_by_date.setdefault(str(point["date"]), []).append(1.0 if oriented_momentum > 0 else 0.0)

    score_points: list[dict[str, float | str]] = []
    for date_text in sorted(by_date_block):
        block_scores = {
            block: mean(scores)
            for block, scores in by_date_block[date_text].items()
            if scores and block in HISTORICAL_BLOCK_WEIGHTS
        }
        if len(block_scores) < 5:
            continue
        weight_sum = sum(HISTORICAL_BLOCK_WEIGHTS[block] for block in block_scores)
        weighted_score = sum(block_scores[block] * HISTORICAL_BLOCK_WEIGHTS[block] for block in block_scores) / weight_sum
        breadth = mean(breadth_by_date.get(date_text, [0.5]))
        acceleration_bonus = 1.6 * (breadth - 0.5)
        weighted_score += acceleration_bonus
        expansion_blocks = ["Growth", "Labor", "Financial Conditions"]
        if all(block_scores.get(block, 0) >= 5.0 for block in expansion_blocks) and breadth >= 0.55:
            weighted_score += 0.75
        score_points.append({"date": date_text, "value": round(max(1.0, min(10.0, weighted_score)), 2)})

    if score_points:
        latest = score_points[-1]["value"]
        adjustment = current_score - float(latest)
        for point in score_points:
            point["value"] = round(max(1.0, min(10.0, float(point["value"]) + adjustment)), 2)
    return score_points
