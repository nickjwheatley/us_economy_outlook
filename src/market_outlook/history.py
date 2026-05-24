from __future__ import annotations

from datetime import date
from math import pi, sin

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


def _score_path(index: int, total: int, date_text: str, current_score: float) -> float:
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


def _indicator_value(
    series: SourceSeries,
    snapshot: IndicatorSnapshot,
    index: int,
    total: int,
    date_text: str,
) -> float:
    progress = index / max(total - 1, 1)
    cycle = sin(progress * 5.0 * pi)
    shorter_cycle = sin(progress * 21.0 * pi)
    recession_pressure = 1.0 if _in_recession(date_text) else 0.0
    direction = 1 if series.higher_is_better else -1

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
    months: int = 240,
) -> dict[str, object]:
    end_year, end_month = _latest_month(snapshots)
    dates = month_sequence(end_year, end_month, months)
    score_points = [
        {"date": date_text, "value": _score_path(index, len(dates), date_text, result.headline_score)}
        for index, date_text in enumerate(dates)
    ]

    indicators: dict[str, object] = {}
    for series_id, snapshot in snapshots.items():
        series = registry.get(series_id)
        if series is None:
            continue
        indicators[series_id] = {
            "name": series.indicator_name,
            "block": series.block,
            "unit": series.value_unit,
            "higherIsBetter": series.higher_is_better,
            "points": [
                {
                    "date": date_text,
                    "value": _indicator_value(series, snapshot, index, len(dates), date_text),
                }
                for index, date_text in enumerate(dates)
            ],
        }

    return {
        "score": score_points,
        "indicators": indicators,
        "recessions": RECESSION_PERIODS,
    }
