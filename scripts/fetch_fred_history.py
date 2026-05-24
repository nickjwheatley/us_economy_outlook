from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "source_registry.csv"
OUT = ROOT / "data" / "fixtures" / "historical_indicators.csv"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"


def month_key(date_text: str) -> str:
    parsed = date.fromisoformat(date_text)
    return date(parsed.year, parsed.month, 1).isoformat()


def is_fred_series(row: dict[str, str]) -> bool:
    return "fred.stlouisfed.org/series/" in row["source_url"]


def read_registry() -> list[dict[str, str]]:
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fetch_series(series_id: str) -> list[dict[str, str]]:
    url = FRED_CSV.format(series_id=series_id)
    try:
        with urlopen(url, timeout=30) as response:
            text = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"skip {series_id}: {error}")
        return []

    reader = csv.DictReader(text.splitlines())
    monthly_last: dict[str, str] = {}
    for row in reader:
        value = row.get(series_id, "").strip()
        observation_date = row.get("observation_date", "").strip()
        if not observation_date or not value or value == ".":
            continue
        monthly_last[month_key(observation_date)] = value

    return [
        {"series_id": series_id, "date": observation_date, "value": value}
        for observation_date, value in sorted(monthly_last.items())
    ]


def main() -> None:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in read_registry():
        series_id = item["series_id"]
        if series_id in seen or not is_fred_series(item):
            continue
        seen.add(series_id)
        rows.extend(fetch_series(series_id))

    by_series = defaultdict(int)
    for row in rows:
        by_series[row["series_id"]] += 1
    print(f"wrote {len(rows)} observations across {len(by_series)} FRED series")
    for series_id, count in sorted(by_series.items()):
        print(f"{series_id}: {count}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series_id", "date", "value"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
