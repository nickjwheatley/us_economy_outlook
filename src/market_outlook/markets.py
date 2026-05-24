from __future__ import annotations

import csv
from math import sqrt
from pathlib import Path

SCORE_BUCKETS = [
    {"label": "<= 3.5", "min": None, "max": 3.5},
    {"label": "3.5-5.0", "min": 3.5, "max": 5.0},
    {"label": "5.0-6.5", "min": 5.0, "max": 6.5},
    {"label": "> 6.5", "min": 6.5, "max": None},
]


def load_market_prices(path: str | Path) -> dict[str, dict[str, object]]:
    prices: dict[str, dict[str, object]] = {}
    price_path = Path(path)
    if not price_path.exists():
        return prices
    with price_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = row.get("adj_close", "").strip()
            if not value:
                continue
            symbol = row["symbol"]
            payload = prices.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": row["name"],
                    "category": row["category"],
                    "source": row["source"],
                    "points": [],
                },
            )
            payload["points"].append({"date": row["date"], "value": round(float(value), 4)})
    return prices


def build_market_relationships(
    score_points: list[dict[str, float | str]],
    market_prices: dict[str, dict[str, object]],
) -> dict[str, object]:
    score_by_date = {str(point["date"]): float(point["value"]) for point in score_points}
    assets: dict[str, object] = {}
    for symbol, payload in market_prices.items():
        aligned = [
            {"date": str(point["date"]), "price": float(point["value"]), "score": score_by_date[str(point["date"])]}
            for point in payload["points"]
            if str(point["date"]) in score_by_date
        ]
        if len(aligned) < 36:
            continue
        assets[symbol] = {
            "symbol": symbol,
            "name": payload["name"],
            "category": payload["category"],
            "source": payload["source"],
            "points": aligned,
            "correlations": {
                "6m": _forward_return_correlation(aligned, 6),
                "12m": _forward_return_correlation(aligned, 12),
                "24m": _forward_return_correlation(aligned, 24),
            },
            "buckets12m": _bucket_forward_returns(aligned, 12),
        }
    return {"assets": assets, "bucketLabels": [bucket["label"] for bucket in SCORE_BUCKETS]}


def _forward_return_correlation(points: list[dict[str, float | str]], months: int) -> dict[str, float | int | None]:
    pairs = _forward_return_pairs(points, months)
    if len(pairs) < 12:
        return {"correlation": None, "n": len(pairs)}
    return {
        "correlation": round(_correlation([score for score, _ in pairs], [return_value for _, return_value in pairs]), 3),
        "n": len(pairs),
    }


def _bucket_forward_returns(points: list[dict[str, float | str]], months: int) -> list[dict[str, float | int | str | None]]:
    pairs = [
        {"score": score, "return": return_value}
        for score, return_value in _forward_return_pairs(points, months)
    ]
    bucket_rows: list[dict[str, float | int | str | None]] = []
    for bucket in SCORE_BUCKETS:
        values = [
            item["return"]
            for item in pairs
            if (bucket["min"] is None or item["score"] > bucket["min"])
            and (bucket["max"] is None or item["score"] <= bucket["max"])
        ]
        bucket_rows.append(
            {
                "bucket": bucket["label"],
                "count": len(values),
                "avgReturn": round(sum(values) / len(values), 4) if values else None,
                "medianReturn": round(sorted(values)[len(values) // 2], 4) if values else None,
            }
        )
    return bucket_rows


def _forward_return_pairs(points: list[dict[str, float | str]], months: int) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for index, point in enumerate(points):
        forward_index = index + months
        if forward_index >= len(points):
            continue
        price = float(point["price"])
        if price == 0:
            continue
        forward_return = (float(points[forward_index]["price"]) / price) - 1
        pairs.append((float(point["score"]), forward_return))
    return pairs


def _correlation(xs: list[float], ys: list[float]) -> float:
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    covariance = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    x_variance = sum((x - x_mean) ** 2 for x in xs)
    y_variance = sum((y - y_mean) ** 2 for y in ys)
    if not x_variance or not y_variance:
        return 0.0
    return covariance / sqrt(x_variance * y_variance)
