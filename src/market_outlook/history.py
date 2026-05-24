from __future__ import annotations

import csv
from datetime import date
from math import pi, sin
from pathlib import Path

from .models import IndicatorSnapshot, OutlookResult, SourceSeries

RECESSION_PERIODS = [
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


def _in_recession(date_text: str) -> bool:
    return any(period["start"] <= date_text <= period["end"] for period in RECESSION_PERIODS)


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
                }
            )
    return points


def _fallback_score_path(index: int, total: int, date_text: str, current_score: float) -> float:
    progress = index / max(total - 1, 1)
    cyclical = 6.2 + 0.9 * sin(progress * 5.4 * pi) + 0.35 * sin(progress * 17.0 * pi)
    if "2008" in date_text:
        cyclical -= 1.6
    if _in_recession(date_text):
        cyclical -= 2.2
    if date_text >= "2022-01-01":
        cyclical -= 0.75 * ((date.fromisoformat(date_text).year - 2022) / 4)
    anchored = cyclical * (1 - progress**3) + current_score * (progress**3)
    return round(max(1.0, min(10.0, anchored)), 2)


def _phase_for(series_id: str) -> float:
    return (sum(ord(char) for char in series_id) % 29) / 29


def _indicator_value(
    series_id: str,
    series: SourceSeries,
    snapshot: IndicatorSnapshot,
    index: int,
    total: int,
    date_text: str,
) -> float:
    progress = index / max(total - 1, 1)
    phase = _phase_for(series_id)
    cycle = sin((progress * (3.5 + phase * 2.0) + phase) * pi)
    shorter_cycle = sin((progress * (13.0 + phase * 11.0) + phase * 0.5) * pi)
    recession_pressure = 1.0 if _in_recession(date_text) else 0.0
    direction = 1 if series.higher_is_better else -1

    if series_id == "T10Y2Y":
        base = snapshot.value + 1.4 * sin((progress * 3.0 + 0.2) * pi)
        if _in_recession(date_text):
            base += 1.1
        if "2019" in date_text or date_text >= "2022-01-01":
            base -= 1.0
        return round(base * (1 - progress**2) + snapshot.value * (progress**2), 2)

    if series.value_unit in {"%", "pp", "% GDP", "% disposable income"}:
        amplitude = max(abs(snapshot.value) * 0.12, 0.35)
        raw = snapshot.value - direction * amplitude * cycle + (-direction) * recession_pressure * amplitude * 1.7
        raw += shorter_cycle * amplitude * 0.25
        value = raw * (1 - progress**2) + snapshot.value * (progress**2)
        return round(max(0.0, value), 2)

    amplitude = max(abs(snapshot.value) * 0.11, 1.0)
    raw = snapshot.value - direction * amplitude * cycle + (-direction) * recession_pressure * amplitude * 0.9
    raw += shorter_cycle * amplitude * 0.15
    value = raw * (1 - progress**2) + snapshot.value * (progress**2)
    return round(max(0.0, value), 2)


def generate_dashboard_history(
    registry: dict[str, SourceSeries],
    snapshots: dict[str, IndicatorSnapshot],
    result: OutlookResult,
    historical_points: dict[str, list[dict[str, float | str]]] | None = None,
    months: int = 240,
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
            points = real_points
            history_source = "FRED monthly history"
        else:
            points = [
                {
                    "date": date_text,
                    "value": _indicator_value(series_id, series, snapshot, index, len(dates), date_text),
                }
                for index, date_text in enumerate(dates)
            ]
            history_source = "synthetic fallback"
        indicators[series_id] = {
            "name": series.indicator_name,
            "block": series.block,
            "unit": series.value_unit,
            "higherIsBetter": series.higher_is_better,
            "historySource": history_source,
            "points": points,
        }

    score_points = _score_from_indicator_history(registry, indicators, result.headline_score)
    if not score_points:
        score_points = [
            {"date": date_text, "value": _fallback_score_path(index, len(dates), date_text, result.headline_score)}
            for index, date_text in enumerate(dates)
        ]

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
