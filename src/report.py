"""Generate a concise executive report from the control-tower warehouse."""

from __future__ import annotations

import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "control_tower.db"
REPORT_DIR = ROOT / "reports"


def fetch_all(connection: sqlite3.Connection, query: str):
    cursor = connection.execute(query)
    return [column[0] for column in cursor.description], cursor.fetchall()


def markdown_table(columns, rows) -> str:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def html_table(columns, rows) -> str:
    head = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def generate_report() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError("Run `python src/pipeline.py` before generating the report.")

    with sqlite3.connect(DB_PATH) as connection:
        kpi_columns, kpi_rows = fetch_all(connection, """
            SELECT COUNT(*) AS orders,
                   ROUND(100.0*SUM(order_status='Delivered')/COUNT(*),1) AS fulfillment_pct,
                   ROUND(100.0*AVG(CASE WHEN order_status='Delivered' THEN delivery_date<=promised_date END),1) AS on_time_pct,
                   ROUND(AVG(CASE WHEN order_status='Delivered' THEN julianday(delivery_date)-julianday(order_date) END),1) AS cycle_days,
                   ROUND(SUM(COALESCE(shipping_cost,0)),0) AS shipping_cost
            FROM orders LEFT JOIN shipments USING(order_id)
        """)
        warehouse_columns, warehouse_rows = fetch_all(connection, """
            SELECT w.warehouse_name AS warehouse, COUNT(*) AS orders,
                   ROUND(100.0*AVG(CASE WHEN o.order_status='Delivered' THEN sh.delivery_date<=o.promised_date END),1) AS on_time_pct,
                   ROUND(AVG(sh.shipping_cost),2) AS avg_ship_cost,
                   ROUND(AVG(CASE WHEN o.order_status='Delivered' THEN julianday(sh.delivery_date)-julianday(o.order_date) END),1) AS cycle_days
            FROM warehouses w JOIN orders o USING(warehouse_id) LEFT JOIN shipments sh USING(order_id)
            GROUP BY w.warehouse_id ORDER BY on_time_pct
        """)
        risk_columns, risk_rows = fetch_all(connection, """
            SELECT w.warehouse_name AS warehouse,
                   SUM(CASE WHEN (i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0)<7 THEN 1 ELSE 0 END) AS critical_skus,
                   ROUND(AVG((i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0)),1) AS avg_days_supply
            FROM inventory_snapshots i JOIN warehouses w USING(warehouse_id)
            GROUP BY w.warehouse_id ORDER BY critical_skus DESC
        """)

    kpis = dict(zip(kpi_columns, kpi_rows[0]))
    worst = warehouse_rows[0]
    total_critical = sum(row[1] for row in risk_rows)
    findings = [
        f"The network delivered **{kpis['on_time_pct']}%** of completed orders on time.",
        f"**{worst[0]}** is the primary service-risk location at **{worst[2]}%** on-time delivery and a **{worst[4]}-day** average cycle.",
        f"The latest inventory snapshot contains **{total_critical} critical SKUs** with fewer than seven available days of supply.",
        "Prioritize West Coast carrier and process review, then expedite inbound inventory for critical SKUs before increasing broad safety stock.",
    ]
    markdown = f"""# Executive Supply Chain Brief

Generated from the reproducible control-tower dataset.

## Network KPIs

{markdown_table(kpi_columns, kpi_rows)}

## Key findings

""" + "\n".join(f"- {finding}" for finding in findings) + f"""

## Warehouse performance

{markdown_table(warehouse_columns, warehouse_rows)}

## Inventory exposure

{markdown_table(risk_columns, risk_rows)}

## Recommended actions

1. Review West Coast DC pick/pack time and carrier transit performance.
2. Create daily alerts for SKUs below seven days of available supply.
3. Track on-time delivery and damage rate by warehouse-carrier pair.
4. Validate improvements against the current network baseline.
"""

    cards = "".join(
        f'<div class="card"><span>{html.escape(label.replace("_", " ").title())}</span><strong>{value}</strong></div>'
        for label, value in kpis.items()
    )
    findings_html = "".join(f"<li>{html.escape(item.replace('**', ''))}</li>" for item in findings)
    dashboard = f"""<!doctype html><html><head><meta charset="utf-8"><title>Supply Chain Control Tower</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f3f6fa;color:#162033;margin:0;padding:32px}}main{{max-width:1100px;margin:auto}}
h1{{margin-bottom:4px}}.subtitle{{color:#5c677d;margin-top:0}}.cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:24px 0}}
.card,section{{background:white;border-radius:10px;padding:18px;box-shadow:0 2px 10px #1b2b4b14}}.card span{{display:block;color:#667085;font-size:12px}}.card strong{{font-size:24px}}
section{{margin:18px 0}}table{{border-collapse:collapse;width:100%}}th,td{{padding:10px;border-bottom:1px solid #e5e9f0;text-align:left}}th{{background:#edf2f7}}li{{margin:9px 0}}
@media(max-width:800px){{.cards{{grid-template-columns:1fr 1fr}}}}
</style></head><body><main><h1>Supply Chain Control Tower</h1><p class="subtitle">Executive operations snapshot · 2025 synthetic portfolio dataset</p>
<div class="cards">{cards}</div><section><h2>Management findings</h2><ul>{findings_html}</ul></section>
<section><h2>Warehouse performance</h2>{html_table(warehouse_columns, warehouse_rows)}</section>
<section><h2>Inventory exposure</h2>{html_table(risk_columns, risk_rows)}</section></main></body></html>"""

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "executive_summary.md").write_text(markdown, encoding="utf-8")
    (REPORT_DIR / "dashboard.html").write_text(dashboard, encoding="utf-8")
    print(f"Reports written to {REPORT_DIR}.")


if __name__ == "__main__":
    generate_report()

