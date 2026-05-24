# Data Sources

This file tracks public economic and market data used by the outlook model.

The canonical machine-readable registry is `data/source_registry.csv`.
The dashboard historical fixture is `data/fixtures/historical_indicators.csv`.

## Current MVP Sources

- FRED-hosted BLS labor series
- FRED-hosted BEA growth and inflation series
- FRED-hosted Treasury and credit-market series
- FRED-hosted housing and sentiment proxies
- FRED-hosted Federal Reserve delinquency and household debt-service series
- Public market valuation sources, including Shiller CAPE and market-cap-to-GDP proxies

## Production Requirements

- Store raw API responses.
- Track source URL, release timestamp, retrieval timestamp, and vintage.
- Flag stale data by expected release frequency.
- Prefer ALFRED vintages for historical backtests where revisions matter.
- Record licensing constraints for non-government or semi-public data.

## Historical Chart Data

Run `py scripts/fetch_fred_history.py` to refresh monthly history for FRED-backed indicators. The dashboard indicator selector only shows indicators with real historical data covering most of the 20-year window. Indicators without sufficient history remain in the current score/table but are omitted from historical charts until real history is wired in.

## Debt And Delinquency Series

The MVP includes:

- `DRCCLACBS`: credit card delinquency rate.
- `DRALACBS`: all-loan delinquency rate.
- `TDSP`: household debt service payments as a share of disposable personal income.

## Market Valuation Series

The MVP includes:

- `CAPE`: Shiller cyclically adjusted price/earnings ratio.
- `SP500FPE`: S&P 500 forward price/earnings ratio.
- `BUFFETT`: broad US equity market capitalization to GDP.
- `ERP`: equity risk premium estimate.

These indicators are not pure recession signals. They primarily shape the VTI and forward-return interpretation: expensive markets can still rise, but high starting valuations tend to reduce long-horizon expected returns and increase vulnerability to earnings or rate disappointment.
