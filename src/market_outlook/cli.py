from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .dashboard import render_dashboard
from .history import generate_dashboard_history
from .io import load_indicator_snapshot, load_source_registry
from .scoring import compute_outlook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic US economic outlook score.")
    parser.add_argument("--registry", default="data/source_registry.csv", help="Path to source registry CSV.")
    parser.add_argument("--snapshot", default="data/fixtures/latest_indicators.csv", help="Path to indicator snapshot CSV.")
    parser.add_argument("--out", default="outputs/dashboard.html", help="Path for generated HTML dashboard.")
    parser.add_argument("--json-out", default="outputs/outlook.json", help="Path for generated JSON result.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = load_source_registry(args.registry)
    snapshots = load_indicator_snapshot(args.snapshot)
    result = compute_outlook(registry, snapshots)
    history = generate_dashboard_history(registry, snapshots, result)

    html_path = Path(args.out)
    json_path = Path(args.json_out)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    html_path.write_text(render_dashboard(result, history), encoding="utf-8")
    json_path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")

    print(f"score={result.headline_score:.2f}")
    print(f"regime={result.regime}")
    print(f"recession_risk={result.recession_risk}")
    print(f"dashboard={html_path}")
    print(f"json={json_path}")


if __name__ == "__main__":
    main()
