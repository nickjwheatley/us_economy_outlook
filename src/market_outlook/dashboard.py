from __future__ import annotations

import json
from html import escape

from .models import OutlookResult


def render_dashboard(result: OutlookResult, history: dict[str, object] | None = None) -> str:
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
    history_json = json.dumps(history or {"score": [], "indicators": {}, "recessions": []})

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
    .chart-grid {{ display: grid; grid-template-columns: 1fr; gap: 16px; }}
    .chart-toolbar {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }}
    .chart-box {{ height: 320px; position: relative; }}
    canvas {{ width: 100%; height: 100%; display: block; }}
    .tooltip {{
      position: fixed;
      display: none;
      pointer-events: none;
      z-index: 20;
      max-width: 220px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.96);
      box-shadow: 0 8px 18px rgba(23, 32, 42, 0.14);
      font-size: 12px;
      color: var(--ink);
    }}
    select {{
      min-width: 260px;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      background: #fff;
      color: var(--ink);
      font: inherit;
    }}
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

    <section class="panel section">
      <div class="chart-toolbar">
        <div>
          <h2>20-Year Economy Score</h2>
          <p class="muted">Recession periods are shaded, FRED-style.</p>
        </div>
      </div>
      <div class="chart-box"><canvas id="scoreChart"></canvas></div>
    </section>

    <section class="panel section">
      <div class="chart-toolbar">
        <div>
          <h2>Indicator History</h2>
          <p class="muted">Select any score input to inspect its 20-year path.</p>
        </div>
        <label class="label" for="indicatorSelect">Indicator</label>
        <select id="indicatorSelect"></select>
      </div>
      <div class="chart-box"><canvas id="indicatorChart"></canvas></div>
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
  <div id="chartTooltip" class="tooltip"></div>
  <script id="dashboard-data" type="application/json">{history_json}</script>
  <script>
    const dashboardData = JSON.parse(document.getElementById("dashboard-data").textContent);
    const axisColor = "#5e6b76";
    const lineColor = "#1f7a8c";
    const recessionColor = "rgba(90, 101, 112, 0.18)";
    const gridColor = "#d9e0e7";
    const chartCache = new Map();

    function resizeCanvas(canvas) {{
      const rect = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * ratio));
      canvas.height = Math.max(1, Math.floor(rect.height * ratio));
      const ctx = canvas.getContext("2d");
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      return {{ ctx, width: rect.width, height: rect.height }};
    }}

    function dateMs(point) {{
      return new Date(point.date + "T00:00:00").getTime();
    }}

    function formatDate(dateText) {{
      return dateText.slice(0, 4);
    }}

    function drawLineChart(canvas, points, options) {{
      if (!points.length) return;
      const {{ ctx, width, height }} = resizeCanvas(canvas);
      const margin = {{ top: 18, right: 18, bottom: 34, left: 54 }};
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;
      const xs = points.map(dateMs);
      const ys = points.map(p => p.value);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const rawMinY = options.minY ?? Math.min(...ys);
      const rawMaxY = options.maxY ?? Math.max(...ys);
      const padY = Math.max((rawMaxY - rawMinY) * 0.10, 0.5);
      const minY = options.minY ?? rawMinY - padY;
      const maxY = options.maxY ?? rawMaxY + padY;
      const xFor = value => margin.left + ((value - minX) / (maxX - minX || 1)) * plotW;
      const yFor = value => margin.top + (1 - ((value - minY) / (maxY - minY || 1))) * plotH;

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, width, height);

      for (const recession of dashboardData.recessions || []) {{
        const start = new Date(recession.start + "T00:00:00").getTime();
        const end = new Date(recession.end + "T00:00:00").getTime();
        const x = Math.max(margin.left, xFor(start));
        const w = Math.min(margin.left + plotW, xFor(end)) - x;
        if (w > 0) {{
          ctx.fillStyle = recessionColor;
          ctx.fillRect(x, margin.top, w, plotH);
        }}
      }}

      ctx.strokeStyle = gridColor;
      ctx.lineWidth = 1;
      ctx.font = "12px Segoe UI, Arial, sans-serif";
      ctx.fillStyle = axisColor;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      for (let i = 0; i <= 4; i++) {{
        const value = minY + ((maxY - minY) * i) / 4;
        const y = yFor(value);
        ctx.beginPath();
        ctx.moveTo(margin.left, y);
        ctx.lineTo(margin.left + plotW, y);
        ctx.stroke();
        ctx.fillText(value.toFixed(options.decimals ?? 1), margin.left - 8, y);
      }}

      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      for (let i = 0; i <= 4; i++) {{
        const x = margin.left + (plotW * i) / 4;
        const pointIndex = Math.min(points.length - 1, Math.round(((points.length - 1) * i) / 4));
        ctx.fillText(formatDate(points[pointIndex].date), x, margin.top + plotH + 12);
      }}

      ctx.strokeStyle = "#aeb8c2";
      ctx.beginPath();
      ctx.moveTo(margin.left, margin.top);
      ctx.lineTo(margin.left, margin.top + plotH);
      ctx.lineTo(margin.left + plotW, margin.top + plotH);
      ctx.stroke();

      ctx.strokeStyle = options.color || lineColor;
      ctx.lineWidth = 2.25;
      ctx.beginPath();
      points.forEach((point, index) => {{
        const x = xFor(dateMs(point));
        const y = yFor(point.value);
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }});
      ctx.stroke();

      if (Number.isInteger(options.hoverIndex)) {{
        const point = points[Math.max(0, Math.min(points.length - 1, options.hoverIndex))];
        const hoverX = xFor(dateMs(point));
        const hoverY = yFor(point.value);
        ctx.strokeStyle = "rgba(23, 32, 42, 0.35)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(hoverX, margin.top);
        ctx.lineTo(hoverX, margin.top + plotH);
        ctx.stroke();
        ctx.fillStyle = options.color || lineColor;
        ctx.beginPath();
        ctx.arc(hoverX, hoverY, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
      }}

      const last = points[points.length - 1];
      ctx.fillStyle = options.color || lineColor;
      ctx.beginPath();
      ctx.arc(xFor(dateMs(last)), yFor(last.value), 4, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#17202a";
      ctx.font = "600 13px Segoe UI, Arial, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(options.title || "", margin.left, 4);
      ctx.fillStyle = axisColor;
      ctx.font = "12px Segoe UI, Arial, sans-serif";
      ctx.fillText(options.subtitle || "", margin.left, 22);

      chartCache.set(canvas.id, {{ points, options, margin, plotW, minX, maxX }});
    }}

    function formatTooltipValue(value, decimals, unit) {{
      const suffix = unit && unit !== "index" && unit !== "ratio" ? ` ${{unit}}` : "";
      return `${{Number(value).toLocaleString(undefined, {{
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }})}}${{suffix}}`;
    }}

    function showTooltip(event, canvas) {{
      const cache = chartCache.get(canvas.id);
      if (!cache || !cache.points.length) return;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const relative = Math.max(0, Math.min(1, (x - cache.margin.left) / (cache.plotW || 1)));
      const hoverIndex = Math.max(0, Math.min(cache.points.length - 1, Math.round(relative * (cache.points.length - 1))));
      const point = cache.points[hoverIndex];
      drawLineChart(canvas, cache.points, {{ ...cache.options, hoverIndex }});

      const tooltip = document.getElementById("chartTooltip");
      tooltip.innerHTML = `<strong>${{cache.options.title || ""}}</strong><br>${{point.date}}<br>${{formatTooltipValue(point.value, cache.options.decimals ?? 1, cache.options.unit || "")}}`;
      tooltip.style.left = `${{event.clientX + 14}}px`;
      tooltip.style.top = `${{event.clientY + 14}}px`;
      tooltip.style.display = "block";
    }}

    function hideTooltip(canvas) {{
      const cache = chartCache.get(canvas.id);
      if (cache) {{
        drawLineChart(canvas, cache.points, cache.options);
      }}
      document.getElementById("chartTooltip").style.display = "none";
    }}

    function installHover(canvas) {{
      canvas.addEventListener("mousemove", event => showTooltip(event, canvas));
      canvas.addEventListener("mouseleave", () => hideTooltip(canvas));
    }}

    function populateIndicatorSelect() {{
      const select = document.getElementById("indicatorSelect");
      const entries = Object.entries(dashboardData.indicators || {{}})
        .sort((a, b) => a[1].block.localeCompare(b[1].block) || a[1].name.localeCompare(b[1].name));
      for (const [id, indicator] of entries) {{
        const option = document.createElement("option");
        option.value = id;
        option.textContent = `${{indicator.block}} - ${{indicator.name}}`;
        select.appendChild(option);
      }}
      const defaultId = entries.find(([id]) => id === "UNRATE")?.[0] || entries[0]?.[0];
      if (defaultId) select.value = defaultId;
    }}

    function drawAllCharts() {{
      drawLineChart(document.getElementById("scoreChart"), dashboardData.score || [], {{
        title: "Economy score",
        subtitle: "1 = depression-like, 10 = robust",
        unit: "score",
        minY: 1,
        maxY: 10,
        decimals: 2
      }});
      const select = document.getElementById("indicatorSelect");
      const indicator = dashboardData.indicators?.[select.value];
      if (indicator) {{
        drawLineChart(document.getElementById("indicatorChart"), indicator.points || [], {{
          title: indicator.name,
          subtitle: `${{indicator.block}} | ${{indicator.unit}} | ${{indicator.historySource}}`,
          unit: indicator.unit,
          color: indicator.higherIsBetter ? "#1f7a8c" : "#8c4f1f",
          decimals: indicator.unit.includes("%") || indicator.unit === "pp" ? 1 : 0
        }});
      }}
    }}

    populateIndicatorSelect();
    document.getElementById("indicatorSelect").addEventListener("change", drawAllCharts);
    window.addEventListener("resize", drawAllCharts);
    drawAllCharts();
    installHover(document.getElementById("scoreChart"));
    installHover(document.getElementById("indicatorChart"));
  </script>
</body>
</html>
"""
