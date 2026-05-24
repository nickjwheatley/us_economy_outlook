from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .models import IndicatorSnapshot, OutlookResult, SourceSeries

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
    by_date: dict[str, list[float]] = {}
    for series_id, payload in indicators.items():
        points = payload["points"]
        if len(points) < 24:
            continue
        values = [float(point["value"]) for point in points]
        low = min(values)
        high = max(values)
        if high == low:
            continue
        series = registry[series_id]
        for point in points:
            raw = (float(point["value"]) - low) / (high - low)
            oriented = raw if series.higher_is_better else 1 - raw
            by_date.setdefault(str(point["date"]), []).append(1 + 9 * oriented)

    score_points: list[dict[str, float | str]] = []
    for date_text in sorted(by_date):
        scores = by_date[date_text]
        if len(scores) < 6:
            continue
        score_points.append({"date": date_text, "value": round(sum(scores) / len(scores), 2)})

    if score_points:
        latest = score_points[-1]["value"]
        adjustment = current_score - float(latest)
        for point in score_points:
            point["value"] = round(max(1.0, min(10.0, float(point["value"]) + adjustment)), 2)
    return score_points
