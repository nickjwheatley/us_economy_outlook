# Scoring Methodology

The headline score blends a transparent rules score and a deterministic prototype ML regime score.

## Rules Score

Indicator scores are averaged into block scores, then weighted:

```text
Growth: 18%
Labor: 18%
Inflation: 13%
Financial Conditions: 14%
Consumer and Business Health: 9%
Housing and Credit: 10%
Fiscal and Policy: 4%
Market Valuation: 9%
Stress Signals: 5%
```

If a block has no indicators in the current snapshot, the rules score renormalizes across populated blocks.

Each indicator score now includes both level and trajectory. The dashboard displays raw Q/Q and Y/Y changes, while scoring uses normalized trajectory signals so a low-but-rising unemployment rate, delinquency rate, or credit spread scores worse than the same level moving in the right direction.

Market valuation is included as a modest-weight block because it matters more for asset-market forward returns than for real economic activity. Expensive markets should not be interpreted as recessionary by themselves, but they lower the margin of safety for VTI-style broad equity exposure.

## ML Regime Score

The MVP includes a deterministic logistic recession-risk prototype based on block scores. This is not yet a trained production model. It exists to establish the model interface and dashboard plumbing.

```text
headline_score = 0.75 * rules_score + 0.25 * ml_regime_score
```

## Regime Mapping

```text
1.0-2.4: depression-like or systemic crisis
2.5-3.9: recessionary
4.0-4.9: stall-speed slowdown
5.0-6.4: mixed or slowing expansion
6.5-8.4: healthy expansion
8.5-10.0: robust expansion
```
