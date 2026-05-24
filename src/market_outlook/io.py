from __future__ import annotations

import csv
from pathlib import Path

from .models import IndicatorSnapshot, SourceSeries


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def load_source_registry(path: str | Path) -> dict[str, SourceSeries]:
    rows: dict[str, SourceSeries] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            series = SourceSeries(
                series_id=row["series_id"],
                source=row["source"],
                source_url=row["source_url"],
                block=row["block"],
                indicator_name=row["indicator_name"],
                frequency=row["frequency"],
                higher_is_better=_to_bool(row["higher_is_better"]),
                leading_or_lagging=row["leading_or_lagging"],
                value_unit=row["value_unit"],
                change_unit=row["change_unit"],
                notes=row["notes"],
            )
            rows[series.series_id] = series
    return rows


def load_indicator_snapshot(path: str | Path) -> dict[str, IndicatorSnapshot]:
    rows: dict[str, IndicatorSnapshot] = {}
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            snapshot = IndicatorSnapshot(
                series_id=row["series_id"],
                as_of=row["as_of"],
                value=float(row["value"]),
                qoq_change=float(row["qoq_change"]),
                yoy_change=float(row["yoy_change"]),
                qoq_signal=float(row["qoq_signal"]),
                yoy_signal=float(row["yoy_signal"]),
                z_score=float(row["z_score"]),
                momentum_3m=float(row["momentum_3m"]),
                momentum_6m=float(row["momentum_6m"]),
                momentum_12m=float(row["momentum_12m"]),
                threshold_distance=float(row["threshold_distance"]),
                freshness_days=int(row["freshness_days"]),
            )
            rows[snapshot.series_id] = snapshot
    return rows
