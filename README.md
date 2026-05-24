# Market Outlook

Deterministic prototype for scoring the US 6-12 month economic outlook on a 1-10 scale.

The current MVP runs offline from a fixture snapshot and produces:

- A headline macro score.
- Economic block scores.
- SaaS revenue-risk interpretation.
- VTI / total-market interpretation.
- A static HTML dashboard.
- 30-year dashboard charts for the economy score and any selected input indicator.

## Run

From this directory:

```powershell
$env:PYTHONPATH='src'
py -m market_outlook.cli --snapshot data/fixtures/latest_indicators.csv --out outputs/dashboard.html
```

Then open `outputs/dashboard.html` in a browser.

To refresh FRED-backed historical chart data:

```powershell
py scripts/fetch_fred_history.py
```

To refresh monthly ETF and sector price histories:

```powershell
py scripts/fetch_market_history.py
```

## Project Shape

- `data/source_registry.csv`: public source registry and canonical series metadata.
- `data/fixtures/latest_indicators.csv`: deterministic offline input snapshot.
- `src/market_outlook`: scoring, interpretation, and dashboard-generation code.
- `docs`: methodology and planning documents.
- `tests`: deterministic unit tests.

## Important Note

The fixture data is an illustrative offline snapshot used to prove the pipeline. Live production use should replace it with API-backed data ingestion, vintage tracking, and audited source timestamps.
