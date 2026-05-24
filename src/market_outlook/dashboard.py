from __future__ import annotations

from html import escape

from .models import OutlookResult


def render_dashboard(result: OutlookResult) -> str:
    def format_value(value: float, unit: str) -> str:
        if unit in {"%", "pp"}:
            return f"{value:.2f}{unit}"
        return f"{value:,.2f} {escape(unit)}"

    def format_change(value: float, unit: str) -> str:
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.2f}{unit}"

    block_rows = "\n".join(
        f"<tr><td>{escape(b.block)}</td><td>{b.score:.2f}</td><td>{b.weight:.0%}</td><td>{b.contribution:.3f}</td></tr>"
        for b in result.block_scores
    )
    indicator_rows = "\n".join(
        "<tr>"
        f"<td>{escape(i.indicator_name)}</td>"
        f"<td>{escape(i.block)}</td>"
        f"<td>{i.score:.2f}</td>"
        f"<td>{escape(i.as_of)}</td>"
        f"<td>{format_value(i.value, i.value_unit)}</td>"
        f"<td>{format_change(i.qoq_change, i.change_unit)}</td>"
        f"<td>{format_change(i.yoy_change, i.change_unit)}</td>"
        f"<td>{i.trajectory_score:+.2f}</td>"
        f"<td>{escape(i.rationale)}</td>"
        "</tr>"
        for i in sorted(result.indicator_scores, key=lambda item: (item.block, item.indicator_name))
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>US Economic Outlook Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5e6b76;
      --line: #d9e0e7;
      --panel: #ffffff;
      --page: #f4f7f9;
      --accent: #1f7a8c;
      --warn: #b85c00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: var(--page);
      color: var(--ink);
      letter-spacing: 0;
    }}
    header {{
      padding: 28px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: #eef4f6;
    }}
    main {{ padding: 24px 32px 40px; max-width: 1280px; margin: 0 auto; }}
    h1, h2 {{ margin: 0; font-weight: 700; }}
    h1 {{ font-size: 28px; }}
    h2 {{ font-size: 18px; margin-bottom: 12px; }}
    p {{ line-height: 1.5; }}
    .muted {{ color: var(--muted); }}
    .grid {{ display: grid; gap: 16px; }}
    .summary {{ grid-template-columns: 220px 1fr 1fr; align-items: stretch; }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .score {{
      font-size: 72px;
      line-height: 1;
      color: var(--accent);
      font-weight: 800;
    }}
    .label {{ font-size: 13px; color: var(--muted); text-transform: uppercase; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; color: var(--muted); text-transform: uppercase; }}
    .section {{ margin-top: 20px; }}
    .risk {{ color: var(--warn); font-weight: 700; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }}
    .table-wrap table {{ min-width: 980px; }}
    @media (max-width: 850px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .summary {{ grid-template-columns: 1fr; }}
      .score {{ font-size: 56px; }}
      table {{ font-size: 14px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>US Economic Outlook</h1>
    <p class="muted">Deterministic 6-12 month macro score prototype</p>
  </header>
  <main>
    <section class="grid summary">
      <div class="panel">
        <div class="label">Headline score</div>
        <div class="score">{result.headline_score:.1f}</div>
        <div class="muted">1 depression-like, 10 robust</div>
      </div>
      <div class="panel">
        <div class="label">Regime</div>
        <h2>{escape(result.regime.title())}</h2>
        <p>Recession risk: <span class="risk">{escape(result.recession_risk)}</span></p>
        <p class="muted">Model probability: {result.recession_probability:.1%}</p>
      </div>
      <div class="panel">
        <div class="label">Market read-through</div>
        <p>{escape(result.vti_implication)}</p>
      </div>
    </section>

    <section class="panel section">
      <h2>Model Blend</h2>
      <p>Rules score: {result.rules_score:.2f} | ML regime score: {result.ml_regime_score:.2f}</p>
    </section>

    <section class="panel section">
      <h2>SaaS Revenue Implication</h2>
      <p>{escape(result.saas_implication)}</p>
    </section>

    <section class="section">
      <h2>Block Scores</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Block</th><th>Score</th><th>Weight</th><th>Contribution</th></tr></thead>
          <tbody>{block_rows}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Indicator Detail</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Indicator</th><th>Block</th><th>Score</th><th>As Of</th><th>Current Value</th><th>Q/Q</th><th>Y/Y</th><th>Trajectory</th><th>Rationale</th></tr></thead>
          <tbody>{indicator_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>
"""
