"""Generate executive Markdown, HTML, and SVG reporting artifacts."""

from __future__ import annotations

import html
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import analytics

DB_PATH = ROOT / "data" / "control_tower.db"
REPORT_DIR = ROOT / "reports"


def markdown_table(columns, rows) -> str:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def html_table(columns, rows, priority_column: int | None = None) -> str:
    head = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    rendered_rows = []
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            css = ""
            if priority_column == index:
                css = ' class="critical"' if str(value).startswith("P1") else ' class="watch"'
            cells.append(f"<td{css}>{html.escape(str(value))}</td>")
        rendered_rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rendered_rows)}</tbody></table>"


def svg_preview(kpis: dict, warehouses: list[tuple], scenario: dict) -> str:
    bars = []
    colors = ["#ef4444", "#f59e0b", "#10b981"]
    for index, row in enumerate(warehouses):
        name, _, rate, _, _ = row
        y = 310 + index * 54
        bars.append(
            f'<text x="55" y="{y+18}" class="label">{html.escape(name)}</text>'
            f'<rect x="250" y="{y}" width="{rate*5.3:.0f}" height="25" rx="5" fill="{colors[index]}"/>'
            f'<text x="{265+rate*5.3:.0f}" y="{y+18}" class="value">{rate}%</text>'
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="560" viewBox="0 0 1000 560">
<style>.title{{font:700 30px Segoe UI,Arial;fill:#f8fafc}}.sub{{font:15px Segoe UI,Arial;fill:#94a3b8}}.kpi{{font:700 29px Segoe UI,Arial;fill:#f8fafc}}.caption{{font:13px Segoe UI,Arial;fill:#94a3b8}}.label{{font:15px Segoe UI,Arial;fill:#cbd5e1}}.value{{font:700 14px Segoe UI,Arial;fill:#f8fafc}}.section{{font:700 18px Segoe UI,Arial;fill:#f8fafc}}</style>
<rect width="1000" height="560" rx="18" fill="#0f172a"/><text x="45" y="55" class="title">Supply Chain Control Tower</text>
<text x="45" y="82" class="sub">Executive snapshot · reproducible 2025 scenario</text>
<g transform="translate(45 115)"><rect width="170" height="105" rx="12" fill="#1e293b"/><text x="18" y="32" class="caption">TOTAL ORDERS</text><text x="18" y="73" class="kpi">{kpis['orders']:,}</text></g>
<g transform="translate(230 115)"><rect width="170" height="105" rx="12" fill="#1e293b"/><text x="18" y="32" class="caption">ON-TIME DELIVERY</text><text x="18" y="73" class="kpi">{kpis['on_time_pct']}%</text></g>
<g transform="translate(415 115)"><rect width="170" height="105" rx="12" fill="#1e293b"/><text x="18" y="32" class="caption">FULFILLMENT</text><text x="18" y="73" class="kpi">{kpis['fulfillment_pct']}%</text></g>
<g transform="translate(600 115)"><rect width="170" height="105" rx="12" fill="#1e293b"/><text x="18" y="32" class="caption">CYCLE TIME</text><text x="18" y="73" class="kpi">{kpis['cycle_days']} days</text></g>
<g transform="translate(785 115)"><rect width="170" height="105" rx="12" fill="#1e293b"/><text x="18" y="32" class="caption">SCENARIO LIFT</text><text x="18" y="73" class="kpi">+{scenario['service_lift_points']} pts</text></g>
<text x="45" y="275" class="section">On-time delivery by distribution center</text>{''.join(bars)}
<rect x="45" y="485" width="910" height="42" rx="8" fill="#172554"/><text x="65" y="512" class="label">Decision case: saving 2 West Coast transit days moves service from {scenario['baseline_on_time_pct']}% to {scenario['scenario_on_time_pct']}% (+{scenario['additional_on_time_orders']} on-time orders).</text>
</svg>'''


def generate_report() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Run `python src/pipeline.py` before generating the report.")
    with sqlite3.connect(DB_PATH) as connection:
        kpis = analytics.network_kpis(connection)
        warehouses = analytics.warehouse_performance(connection)
        carrier_lanes = analytics.carrier_lane_performance(connection)[:8]
        exceptions = analytics.priority_exceptions(connection, 10)
        scenario = analytics.intervention_scenario(connection)

    worst = warehouses[0]
    findings = [
        f"Network on-time delivery is {kpis['on_time_pct']}%; {worst[0]} is the constraint at {worst[2]}%.",
        f"A two-day West Coast transit improvement raises local on-time service to {scenario['scenario_on_time_pct']}%, adding {scenario['additional_on_time_orders']} on-time orders.",
        f"The exception queue ranks {len(exceptions)} immediate actions by estimated gross-margin exposure.",
    ]
    warehouse_columns = ["warehouse", "orders", "on_time_pct", "avg_ship_cost", "cycle_days"]
    carrier_columns = ["warehouse", "carrier", "orders", "on_time_pct", "transit_days", "avg_ship_cost"]
    exception_columns = ["warehouse", "product_id", "product", "days_supply", "lead_time", "daily_margin_risk", "margin_exposure", "priority"]
    scenario_rows = [[key, value] for key, value in scenario.items()]
    markdown = f"""# Executive Supply Chain Brief

Generated from the reproducible control-tower dataset.

![Control tower preview](dashboard_preview.svg)

## Decision summary

""" + "\n".join(f"- {finding}" for finding in findings) + f"""

## Warehouse performance

{markdown_table(warehouse_columns, warehouses)}

## Lowest-performing warehouse/carrier lanes

{markdown_table(carrier_columns, carrier_lanes)}

## Priority exception queue

{markdown_table(exception_columns, exceptions)}

## Two-day transit improvement scenario

{markdown_table(["metric", "value"], scenario_rows)}

## Recommended actions

1. Pilot carrier and fulfillment interventions at West Coast DC.
2. Expedite the highest margin-exposure inventory exceptions first.
3. Review the carrier-lane scorecard weekly rather than relying on network averages.
4. Measure the pilot against the documented baseline before scaling.
"""

    cards = "".join(f'<div class="card"><span>{label.replace("_", " ").title()}</span><strong>{value}</strong></div>' for label, value in kpis.items())
    findings_html = "".join(f"<li>{html.escape(item)}</li>" for item in findings)
    dashboard = f"""<!doctype html><html><head><meta charset="utf-8"><title>Supply Chain Control Tower</title><style>
:root{{--ink:#14213d;--muted:#667085;--navy:#0f172a;--blue:#2563eb;--bg:#eef2f7}}*{{box-sizing:border-box}}body{{font-family:Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink);margin:0}}header{{background:var(--navy);color:white;padding:34px calc((100% - 1180px)/2)}}main{{max-width:1180px;margin:auto;padding:28px}}h1{{margin:0 0 6px}}header p{{color:#cbd5e1;margin:0}}.cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:22px}}.card,section{{background:white;border-radius:12px;padding:18px;box-shadow:0 3px 12px #1b2b4b12}}.card span{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase}}.card strong{{font-size:25px}}section{{margin:18px 0;overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:10px;border-bottom:1px solid #e5e9f0;text-align:left}}th{{background:#f8fafc;color:#475467}}li{{margin:9px 0}}.critical{{color:#b42318;font-weight:700}}.watch{{color:#b54708;font-weight:700}}.scenario{{border-left:5px solid var(--blue)}}@media(max-width:850px){{header{{padding:25px}}.cards{{grid-template-columns:1fr 1fr}}main{{padding:15px}}}}
</style></head><body><header><h1>Supply Chain Control Tower</h1><p>Executive operations snapshot · 2025 synthetic portfolio dataset</p></header><main><div class="cards">{cards}</div>
<section><h2>Management findings</h2><ul>{findings_html}</ul></section><section class="scenario"><h2>Intervention business case</h2>{html_table(["metric", "value"], scenario_rows)}</section>
<section><h2>Warehouse performance</h2>{html_table(warehouse_columns, warehouses)}</section><section><h2>Carrier-lane root cause</h2>{html_table(carrier_columns, carrier_lanes)}</section>
<section><h2>Priority exception queue</h2>{html_table(exception_columns, exceptions, 7)}</section></main></body></html>"""

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "executive_summary.md").write_text(markdown, encoding="utf-8")
    (REPORT_DIR / "dashboard.html").write_text(dashboard, encoding="utf-8")
    (REPORT_DIR / "dashboard_preview.svg").write_text(svg_preview(kpis, warehouses, scenario), encoding="utf-8")
    print(f"Reports written to {REPORT_DIR}.")


if __name__ == "__main__":
    generate_report()

