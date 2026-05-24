# US Economic Outlook Model Plan

## Purpose

Build a deterministic model that produces a 6-12 month outlook score for the US economy on a 1-10 scale:

- `1`: depression-like contraction or systemic crisis
- `2-3`: recessionary conditions likely or already emerging
- `4`: stall-speed economy with elevated downside risk
- `5-6`: mixed or slowing expansion
- `7-9`: healthy expansion
- `10`: robust broad-based expansion

The model should be suitable for a comprehensive dashboard, with transparent drivers, reproducible data inputs, and auditable scoring logic.

## Operating Principles

- The production score must be deterministic: same data vintage, model version, and configuration should produce the same result.
- Machine learning may be used for classification, probability estimation, feature weighting, and regime detection, but the final score must be explainable.
- The system should distinguish between current conditions, leading indicators, and lagging confirmation.
- Public data should be preferred, with source metadata and release timestamps tracked.
- The model should show uncertainty and risk distribution, not only a single point estimate.

## Core Data Sources

Primary public sources:

- FRED / St. Louis Fed: broad macro series, yield curve, credit spreads, recession indicators, financial conditions.
- ALFRED / St. Louis Fed: vintage-aware historical data where revisions matter.
- Bureau of Labor Statistics: payrolls, unemployment, wages, CPI, labor force indicators.
- Bureau of Economic Analysis: GDP, GDI, personal income, consumption, investment, corporate profits, NIPA tables.
- US Treasury Fiscal Data: receipts, outlays, debt, Treasury cash balances, issuance-related series.
- Census Bureau: retail sales, housing starts, building permits, durable goods, construction spending.
- Federal Reserve: industrial production, bank credit, financial accounts, senior loan officer survey, policy rates.
- Public market data: equity indexes, Treasury yields, credit spreads, volatility, commodities, dollar indexes.

Optional sources, subject to licensing and availability:

- ISM manufacturing and services.
- Conference Board leading indicators.
- University of Michigan consumer sentiment.
- NFIB small business data.
- Private-sector SaaS and software spending surveys.

## Indicator Blocks

### Growth

Examples:

- Real GDP
- Real GDI
- Industrial production
- Retail sales
- Real personal consumption expenditures
- Durable goods orders
- Construction spending

Purpose:

Measure whether real economic activity is expanding, slowing, or contracting.

### Labor Market

Examples:

- Nonfarm payrolls
- Unemployment rate
- Initial and continuing claims
- Job openings
- Quits rate
- Wage growth
- Labor force participation

Purpose:

Identify whether household income and employment conditions support spending, and whether labor-market deterioration is accelerating.

### Inflation And Prices

Examples:

- CPI
- Core CPI
- PCE inflation
- Core PCE inflation
- Trimmed mean / median inflation
- Inflation expectations
- Commodity prices

Purpose:

Estimate inflation pressure and the likely constraint it places on monetary policy and real purchasing power.

### Financial Conditions

Examples:

- Treasury yield curve
- Credit spreads
- Equity-market trend
- Volatility
- Real interest rates
- Dollar strength
- Lending standards

Purpose:

Capture the forward-looking transmission channel from markets and credit into real activity.

### Consumer And Business Health

Examples:

- Real disposable income
- Savings rate
- Consumer sentiment
- Small business optimism
- ISM manufacturing
- ISM services

Purpose:

Assess household and business willingness and ability to spend, invest, and hire.

### Housing And Credit

Examples:

- Housing starts
- Building permits
- Mortgage rates
- Housing affordability
- Household debt service
- Delinquencies
- Bank lending growth

Purpose:

Track interest-sensitive demand and credit-cycle stress.

### Fiscal And Policy

Examples:

- Federal deficit impulse
- Government receipts and outlays
- Fed funds rate
- Real policy rate
- Federal Reserve balance sheet
- Treasury issuance pressure

Purpose:

Estimate whether fiscal and monetary policy are adding support or restraint.

### Recession And Stress Signals

Examples:

- Sahm-rule-style labor deterioration
- Yield-curve inversion duration
- Initial claims acceleration
- Credit-spread widening
- Financial stress indexes
- Negative real income momentum

Purpose:

Detect nonlinear deterioration that can turn an ordinary slowdown into recession risk.

## Feature Engineering

For each series, create standardized features:

- Latest level
- 3-month momentum
- 6-month momentum
- 12-month momentum
- Year-over-year change
- Z-score versus historical window
- Percentile rank
- Direction of recent change
- Distance from recession threshold
- Distance from expansion threshold
- Release freshness
- Revision sensitivity
- Historical lead or lag classification

Each feature should carry metadata:

```text
series_id
source
source_url
release_frequency
release_lag
economic_block
transformation
higher_is_better
leading_or_lagging
recession_sensitivity
revision_sensitivity
last_updated_at
data_vintage
```

## Modeling Architecture

### Rules-Based Baseline

The first production model should be a transparent weighted score by block. A starting weight structure:

```text
Growth: 20%
Labor: 20%
Inflation: 15%
Financial Conditions: 15%
Consumer and Business Health: 10%
Housing and Credit: 10%
Fiscal and Policy: 5%
Stress Signals: 5%
```

The rules model should convert each feature into a normalized score, aggregate features into block scores, and aggregate block scores into the headline score.

### Machine Learning Layer

The ML layer should estimate future regime probabilities and help calibrate the headline score.

Candidate targets:

- Recession within 6 months
- Recession within 12 months
- Below-trend growth
- Above-trend growth
- Stagflationary slowdown
- Financial stress regime

Candidate models:

- Regularized logistic regression
- Gradient boosting
- Random forest
- Dynamic factor model
- Principal component model
- Hidden Markov model
- Bayesian model averaging

The ML layer should be trained with walk-forward validation and, where possible, vintage-aware data.

### Final Score

A possible production formula:

```text
final_score =
  0.45 * rules_score
+ 0.35 * ml_regime_score
+ 0.10 * financial_stress_adjustment
+ 0.10 * deterministic_rare_condition_adjustment
```

The rare-condition adjustment should be rule-based, not discretionary. Examples:

- Banking stress event
- Oil shock
- Policy cliff
- Debt-ceiling disruption
- Rapid labor-market break
- Sudden credit-market seizure

## Agent Design

### Data Ingestion Agent

Responsibilities:

- Pull source data from public APIs.
- Store raw responses.
- Track release dates, source timestamps, and vintages.
- Normalize dates, frequencies, and units.

### Data Quality Agent

Responsibilities:

- Detect missing values.
- Detect stale data.
- Detect outliers and suspicious revisions.
- Validate expected release frequencies.
- Flag source failures.

### Feature Engineering Agent

Responsibilities:

- Apply transformations.
- Create momentum, z-score, percentile, and threshold-distance features.
- Maintain feature metadata.
- Ensure feature definitions are versioned.

### Economic Regime Agent

Responsibilities:

- Classify current and forward-looking regimes.
- Identify transitions between expansion, slowdown, recession, recovery, and stress regimes.
- Explain regime changes.

### ML Training Agent

Responsibilities:

- Train and validate models.
- Run walk-forward tests.
- Store model artifacts.
- Track feature importance and calibration.
- Compare ML models against rules baseline.

### Scoring Agent

Responsibilities:

- Produce the headline 1-10 score.
- Produce block-level sub-scores.
- Generate score decomposition.
- Track score changes versus prior run.

### Narrative Agent

Responsibilities:

- Summarize the score in plain economic language.
- Explain top positive and negative drivers.
- Identify watch-list indicators.
- Translate macro score into sector and market implications.

### Dashboard Agent

Responsibilities:

- Render scorecards, charts, heatmaps, and tables.
- Support historical comparison and scenario views.
- Show data freshness and model version.

### Audit And Governance Agent

Responsibilities:

- Record model version.
- Record data vintage.
- Record configuration hash.
- Record source timestamps.
- Preserve run logs.
- Support reproducibility.

### Alerting Agent

Responsibilities:

- Flag major score changes.
- Flag recession-risk jumps.
- Flag breached thresholds.
- Flag data-source failures.

## Dashboard Specification

Required views:

- Headline 1-10 score
- Current economic regime
- 6-month and 12-month recession probability
- Historical score chart
- Indicator block heatmap
- Top positive contributors
- Top negative contributors
- What changed since the prior update
- Indicator detail table
- Data freshness panel
- Model version and run metadata
- Sector implications panel
- Market implications panel
- Scenario comparison panel

Recommended charts:

- Score history with recession shading
- Yield curve and recession-risk overlay
- Credit spreads and financial stress
- Payroll growth and claims
- Inflation versus policy-rate stance
- Housing activity versus mortgage rates
- SaaS revenue-risk sensitivity panel
- VTI valuation and macro-regime panel

## Backtesting Plan

Backtest against:

- NBER recession periods
- GDP slowdowns
- Payroll contractions
- Equity bear markets
- Credit stress episodes
- Inflation shocks
- Soft-landing periods

Validation methods:

- Walk-forward validation
- Vintage-aware testing where available
- Out-of-sample regime classification
- Recession-probability calibration
- Feature-importance stability checks
- False-positive and false-negative analysis

Metrics:

- Recession detection accuracy
- Average lead time before recessions
- False-positive recession warnings
- Score stability
- Calibration error
- Regime-classification accuracy
- Drawdown-warning usefulness

## Documentation Set

Maintain these files during the build:

- `DATA_SOURCES.md`: source endpoints, series IDs, frequencies, licensing notes.
- `INDICATOR_DICTIONARY.md`: meaning and economic interpretation of each indicator.
- `FEATURES.md`: feature formulas and transformation details.
- `SCORING_METHODOLOGY.md`: block weights, thresholds, score mapping, and final formula.
- `MODEL_CARD.md`: model purpose, data, validation, risks, and limitations.
- `DASHBOARD_SPEC.md`: visual design and interaction requirements.
- `RUNBOOK.md`: refresh, retrain, troubleshoot, and publish procedures.
- `GOVERNANCE.md`: versioning, audit trail, and change-control process.
- `SECTOR_AND_MARKET_IMPLICATIONS.md`: macro-score interpretation for sectors and asset classes.

## Implementation Phases

### Phase 1: Baseline Score

- Build data-source registry.
- Ingest a minimal set of high-value public indicators.
- Create feature pipeline.
- Create rules-based score.
- Produce simple dashboard prototype.

### Phase 2: Backtesting

- Add recession labels and historical regimes.
- Run walk-forward validation.
- Calibrate thresholds and score mapping.
- Add historical score visualization.

### Phase 3: ML Regime Model

- Train candidate models.
- Compare ML outputs against rules score.
- Add feature importance and calibration diagnostics.
- Freeze first production model artifact.

### Phase 4: Dashboard And Narrative

- Add dashboard decomposition.
- Add score-change narrative.
- Add sector implications.
- Add market implications.
- Add alerting.

### Phase 5: Governance

- Add model registry.
- Add data-vintage logging.
- Add run reproducibility.
- Add formal documentation and runbook.

## Known Limitations

- Economic data is revised, sometimes materially.
- Public data often arrives with a lag.
- Financial markets are forward-looking but noisy.
- Recession labels are known only after the fact.
- Sector revenue impact varies by company business model, pricing power, customer base, and contract structure.
- The model should support decision-making, not replace judgment.
