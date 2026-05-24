from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "source_registry.csv"
OUT = ROOT / "data" / "fixtures" / "historical_indicators.csv"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
SHILLER_CSV = "https://posix4e.github.io/shiller_wrapper_data/data/stock_market_data.csv"
WORLD_BANK_MARKET_CAP_GDP = (
    "https://api.worldbank.org/v2/country/USA/indicator/CM.MKT.LCAP.GD.ZS?format=json&per_page=100"
)


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
        {"series_id": series_id, "date": observation_date, "value": value, "source": "FRED monthly history"}
        for observation_date, value in sorted(monthly_last.items())
    ]


def fetch_shiller_valuation_series() -> list[dict[str, str]]:
    try:
        with urlopen(SHILLER_CSV, timeout=30) as response:
            text = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"skip Shiller valuation data: {error}")
        return []

    rows: list[dict[str, str]] = []
    for row in csv.reader(text.splitlines()):
        if not row or row[0] == "date_string":
            continue
        if len(row) < 10:
            continue
        observation_date = row[0].strip()
        cape = row[7].strip()
        long_rate = row[9].strip()
        if cape:
            rows.append(
                {
                    "series_id": "CAPE",
                    "date": month_key(observation_date),
                    "value": cape,
                    "source": "Robert Shiller/Yale monthly data",
                }
            )
        if cape and long_rate:
            spread = (100 / float(cape)) - float(long_rate)
            rows.append(
                {
                    "series_id": "CAPE_YIELD_SPREAD",
                    "date": month_key(observation_date),
                    "value": f"{spread:.6f}",
                    "source": "Calculated from Shiller CAPE and 10Y Treasury",
                }
            )
    return rows


def fetch_world_bank_market_cap_to_gdp() -> list[dict[str, str]]:
    try:
        with urlopen(WORLD_BANK_MARKET_CAP_GDP, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"skip World Bank market-cap-to-GDP: {error}")
        return []

    rows: list[dict[str, str]] = []
    for item in payload[1]:
        value = item.get("value")
        if value is None:
            continue
        rows.append(
            {
                "series_id": "BUFFETT",
                "date": f"{item['date']}-01-01",
                "value": f"{float(value):.6f}",
                "source": "World Bank annual data",
            }
        )
    return sorted(rows, key=lambda row: row["date"])


def main() -> None:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in read_registry():
        series_id = item["series_id"]
        if series_id in seen or not is_fred_series(item):
            continue
        seen.add(series_id)
        rows.extend(fetch_series(series_id))
    rows.extend(fetch_shiller_valuation_series())
    rows.extend(fetch_world_bank_market_cap_to_gdp())

    by_series = defaultdict(int)
    for row in rows:
        by_series[row["series_id"]] += 1
    print(f"wrote {len(rows)} observations across {len(by_series)} FRED series")
    for series_id, count in sorted(by_series.items()):
        print(f"{series_id}: {count}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["series_id", "date", "value", "source"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
