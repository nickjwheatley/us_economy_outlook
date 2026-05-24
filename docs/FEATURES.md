# Features

The MVP snapshot uses precomputed feature columns:

- `z_score`: raw standardized current level before direction inversion.
- `qoq_change`: raw quarter-over-quarter change shown in the dashboard.
- `yoy_change`: raw year-over-year change shown in the dashboard.
- `qoq_signal`: normalized quarter-over-quarter trajectory signal used in scoring.
- `yoy_signal`: normalized year-over-year trajectory signal used in scoring.
- `momentum_3m`: recent three-month directional signal.
- `momentum_6m`: six-month directional signal.
- `momentum_12m`: twelve-month directional signal.
- `threshold_distance`: distance from a relevant stress or expansion threshold.
- `freshness_days`: days since the observation was last updated.

## Indicator Score Formula

Each indicator is converted to a 1-10 score:

```text
score =
  5.5
+ 1.20 * directional_z_score
+ 0.80 * average_directional_momentum
+ 0.90 * directional_trajectory
+ 0.70 * threshold_distance
- freshness_penalty
```

The result is clamped to `[1, 10]`.

For indicators where lower values are better, such as unemployment, inflation, credit spreads, delinquency rates, debt-service burden, mortgage rates, and policy rates, the z-score, momentum, and trajectory inputs are directionally inverted before scoring. This means a 4.3% unemployment rate scores worse when it is rising than when it is falling.
