# Runbook

## Run The MVP

```powershell
$env:PYTHONPATH='src'
py -m market_outlook.cli --snapshot data/fixtures/latest_indicators.csv --out outputs/dashboard.html
```

## Run Tests

```powershell
$env:PYTHONPATH='src'
py -m unittest discover -s tests
```

## Outputs

- `outputs/dashboard.html`
- `outputs/outlook.json`

## Troubleshooting

- If `market_outlook` cannot be imported, confirm `PYTHONPATH` includes `src`.
- If a score changes unexpectedly, inspect `outputs/outlook.json` and the fixture snapshot.
- If live ingestion is added, preserve the raw source response before transformation.
