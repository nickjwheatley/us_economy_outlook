from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fixtures" / "market_prices.csv"
YAHOO_CHART = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    "?period1={period1}&period2={period2}&interval=1mo&events=history&includeAdjustedClose=true"
)

ASSETS = [
    ("SPY", "S&P 500 ETF", "Broad market"),
    ("VTI", "Total US Market ETF", "Broad market"),
    ("QQQ", "Nasdaq 100 ETF", "Growth / large-cap tech"),
    ("IGV", "Expanded Tech-Software ETF", "Software"),
    ("IWM", "Russell 2000 ETF", "Small caps"),
    ("XLK", "Technology Select Sector SPDR", "Sector"),
    ("XLF", "Financial Select Sector SPDR", "Sector"),
    ("XLY", "Consumer Discretionary Select Sector SPDR", "Sector"),
    ("XLP", "Consumer Staples Select Sector SPDR", "Sector"),
    ("XLI", "Industrial Select Sector SPDR", "Sector"),
    ("XLV", "Health Care Select Sector SPDR", "Sector"),
    ("XLE", "Energy Select Sector SPDR", "Sector"),
    ("XLU", "Utilities Select Sector SPDR", "Sector"),
    ("XLB", "Materials Select Sector SPDR", "Sector"),
    ("XLRE", "Real Estate Select Sector SPDR", "Sector"),
    ("XLC", "Communication Services Select Sector SPDR", "Sector"),
]


def unix_date(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=timezone.utc).timestamp())


def month_key(timestamp: int) -> str:
    parsed = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return date(parsed.year, parsed.month, 1).isoformat()


def fetch_asset(symbol: str, name: str, category: str) -> list[dict[str, str]]:
    url = YAHOO_CHART.format(
        symbol=symbol,
        period1=unix_date(1995, 1, 1),
        period2=unix_date(2026, 5, 24),
    )
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = payload["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    adjusted = result["indicators"]["adjclose"][0]["adjclose"]
    rows: list[dict[str, str]] = []
    for timestamp, price in zip(timestamps, adjusted):
        if price is None:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": name,
                "category": category,
                "date": month_key(timestamp),
                "adj_close": f"{float(price):.6f}",
                "source": "Yahoo Finance monthly adjusted close",
            }
        )
    return rows


def main() -> None:
    rows: list[dict[str, str]] = []
    for symbol, name, category in ASSETS:
        asset_rows = fetch_asset(symbol, name, category)
        rows.extend(asset_rows)
        print(f"{symbol}: {len(asset_rows)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "name", "category", "date", "adj_close", "source"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
