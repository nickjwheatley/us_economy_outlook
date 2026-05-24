# Governance

## Versioning

Every production run should record:

- Model version
- Data snapshot version
- Source retrieval timestamps
- Data vintages
- Configuration hash
- Code commit hash, once the project is under version control

## Change Control

Changes that require review:

- Indicator additions or removals
- Block weight changes
- Feature formula changes
- ML model retraining
- Regime threshold changes
- Dashboard interpretation changes

## Audit Trail

Each run should preserve:

- Raw source data
- Processed features
- Score output
- Narrative output
- Validation warnings
