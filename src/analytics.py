"""Reusable decision-support queries for the control tower."""

from __future__ import annotations

import sqlite3


def network_kpis(connection: sqlite3.Connection) -> dict[str, float]:
    row = connection.execute("""
        SELECT COUNT(*) AS orders,
               ROUND(100.0*SUM(order_status='Delivered')/COUNT(*),1) AS fulfillment_pct,
               ROUND(100.0*AVG(CASE WHEN order_status='Delivered' THEN delivery_date<=promised_date END),1) AS on_time_pct,
               ROUND(AVG(CASE WHEN order_status='Delivered' THEN julianday(delivery_date)-julianday(order_date) END),1) AS cycle_days,
               ROUND(SUM(COALESCE(shipping_cost,0)),0) AS shipping_cost
        FROM orders LEFT JOIN shipments USING(order_id)
    """).fetchone()
    return dict(zip(("orders", "fulfillment_pct", "on_time_pct", "cycle_days", "shipping_cost"), row))


def warehouse_performance(connection: sqlite3.Connection) -> list[tuple]:
    return connection.execute("""
        SELECT w.warehouse_name, COUNT(*) AS orders,
               ROUND(100.0*AVG(CASE WHEN o.order_status='Delivered' THEN sh.delivery_date<=o.promised_date END),1) AS on_time_pct,
               ROUND(AVG(sh.shipping_cost),2) AS avg_ship_cost,
               ROUND(AVG(CASE WHEN o.order_status='Delivered' THEN julianday(sh.delivery_date)-julianday(o.order_date) END),1) AS cycle_days
        FROM warehouses w JOIN orders o USING(warehouse_id) LEFT JOIN shipments sh USING(order_id)
        GROUP BY w.warehouse_id ORDER BY on_time_pct
    """).fetchall()


def carrier_lane_performance(connection: sqlite3.Connection) -> list[tuple]:
    return connection.execute("""
        SELECT w.warehouse_name, sh.carrier, COUNT(*) AS delivered_orders,
               ROUND(100.0*AVG(sh.delivery_date<=o.promised_date),1) AS on_time_pct,
               ROUND(AVG(julianday(sh.delivery_date)-julianday(sh.ship_date)),1) AS transit_days,
               ROUND(AVG(sh.shipping_cost),2) AS avg_ship_cost
        FROM orders o JOIN shipments sh USING(order_id) JOIN warehouses w USING(warehouse_id)
        WHERE o.order_status='Delivered'
        GROUP BY w.warehouse_id, sh.carrier
        HAVING COUNT(*) >= 25
        ORDER BY on_time_pct, delivered_orders DESC
    """).fetchall()


def priority_exceptions(connection: sqlite3.Connection, limit: int = 10) -> list[tuple]:
    """Rank inventory exceptions by margin exposure and urgency."""
    return connection.execute("""
        SELECT w.warehouse_name, p.product_id, p.product_name,
               ROUND((i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0),1) AS days_supply,
               s.contracted_lead_time_days,
               ROUND(i.avg_daily_demand*(p.unit_price-p.unit_cost),2) AS daily_margin_at_risk,
               ROUND(
                   MAX(0, s.contracted_lead_time_days-
                       (i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0))
                   * i.avg_daily_demand * (p.unit_price-p.unit_cost), 2
               ) AS estimated_margin_exposure,
               CASE
                 WHEN i.on_hand_units-i.allocated_units <= 0 THEN 'P1 Stockout'
                 WHEN (i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0) < 7 THEN 'P1 Critical'
                 WHEN (i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0) < s.contracted_lead_time_days THEN 'P2 Expedite'
                 ELSE 'P3 Monitor'
               END AS priority
        FROM inventory_snapshots i
        JOIN warehouses w USING(warehouse_id)
        JOIN products p USING(product_id)
        JOIN suppliers s USING(supplier_id)
        WHERE (i.on_hand_units-i.allocated_units)/NULLIF(i.avg_daily_demand,0) < s.contracted_lead_time_days
        ORDER BY estimated_margin_exposure DESC, days_supply
        LIMIT ?
    """, (limit,)).fetchall()


def intervention_scenario(connection: sqlite3.Connection, warehouse_name: str = "West Coast DC",
                          transit_days_saved: int = 2) -> dict[str, float]:
    """Estimate service improvement if delivered orders arrive N days sooner."""
    row = connection.execute("""
        WITH order_metrics AS (
            SELECT o.order_id,
                   sh.delivery_date<=o.promised_date AS baseline_on_time,
                   date(sh.delivery_date, ? || ' days')<=o.promised_date AS scenario_on_time,
                   SUM(ol.quantity*(p.unit_price-p.unit_cost)) AS delivered_margin
            FROM orders o
            JOIN shipments sh USING(order_id)
            JOIN warehouses w USING(warehouse_id)
            JOIN order_lines ol USING(order_id)
            JOIN products p USING(product_id)
            WHERE o.order_status='Delivered' AND w.warehouse_name=?
            GROUP BY o.order_id
        )
        SELECT COUNT(*) AS delivered_orders,
               SUM(baseline_on_time), SUM(scenario_on_time),
               ROUND(SUM(delivered_margin),2)
        FROM order_metrics
    """, (f"-{transit_days_saved}", warehouse_name)).fetchone()
    delivered_orders, baseline, scenario, delivered_margin = row
    improvement = scenario - baseline
    return {
        "delivered_orders": delivered_orders,
        "baseline_on_time_pct": round(100 * baseline / delivered_orders, 1),
        "scenario_on_time_pct": round(100 * scenario / delivered_orders, 1),
        "additional_on_time_orders": improvement,
        "service_lift_points": round(100 * improvement / delivered_orders, 1),
        "delivered_margin": delivered_margin,
    }
