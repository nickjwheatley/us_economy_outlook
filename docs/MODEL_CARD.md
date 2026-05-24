# Model Card

## Model

US Economic Outlook MVP, version `0.1.0`.

## Intended Use

Estimate the 6-12 month US economic outlook on a 1-10 scale and provide dashboard-ready interpretation for macro conditions, SaaS revenue sensitivity, and VTI-style broad equity exposure.

## Current Status

Prototype. The current model runs from an illustrative offline fixture and should not be treated as a live economic estimate.

## Inputs

- Public macroeconomic indicators
- Labor-market indicators
- Inflation indicators
- Financial-condition indicators
- Housing and credit indicators
- Policy indicators
- Market valuation indicators

## Outputs

- Headline score
- Rules score
- ML regime score
- Recession probability
- Block scores
- Indicator scores
- SaaS implication
- VTI implication
- Market valuation block score

## Limitations

- Fixture data is illustrative.
- ML layer is a deterministic prototype, not a trained production artifact.
- No data-vintage backtesting has been implemented yet.
- Live API ingestion has not been connected yet.
