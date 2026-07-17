"""Build a reproducible supply-chain control tower dataset and SQLite warehouse."""

from __future__ import annotations

import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
DB_PATH = DATA / "control_tower.db"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
SEED = 42


def write_csv(name: str, rows: list[dict]) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    with (RAW / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def generate_data(order_count: int = 1800) -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    suppliers = [
        {"supplier_id": f"S{i:03}", "supplier_name": name, "region": region,
         "contracted_lead_time_days": lead, "quality_target": quality}
        for i, (name, region, lead, quality) in enumerate([
            ("Northstar Components", "Midwest", 8, .985),
            ("Blue Ridge Manufacturing", "South", 11, .980),
            ("Pacific Source Group", "West", 14, .975),
            ("Atlantic Industrial", "Northeast", 7, .990),
            ("Lone Star Supply", "South", 10, .982),
            ("Great Lakes Goods", "Midwest", 9, .987),
        ], 1)
    ]
    warehouses = [
        {"warehouse_id": "W001", "warehouse_name": "East Coast DC", "state": "PA", "capacity_units": 45000},
        {"warehouse_id": "W002", "warehouse_name": "Central DC", "state": "IL", "capacity_units": 52000},
        {"warehouse_id": "W003", "warehouse_name": "West Coast DC", "state": "NV", "capacity_units": 40000},
    ]
    categories = ["Electronics", "Office", "Industrial", "Safety", "Packaging"]
    products = []
    for i in range(1, 31):
        cost = round(rng.uniform(8, 180), 2)
        products.append({
            "product_id": f"P{i:03}", "product_name": f"{categories[(i-1) % 5]} Item {i:02}",
            "category": categories[(i-1) % 5], "supplier_id": suppliers[(i-1) % 6]["supplier_id"],
            "unit_cost": cost, "unit_price": round(cost * rng.uniform(1.25, 1.65), 2),
            "reorder_point": rng.randint(80, 350),
        })

    orders, lines, shipments = [], [], []
    start = date(2025, 1, 1)
    carriers = ["SwiftFreight", "National Logistics", "RoadRunner", "ParcelPro"]
    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    for i in range(1, order_count + 1):
        order_date = start + timedelta(days=rng.randrange(365))
        promised_days = rng.randint(4, 10)
        promised_date = order_date + timedelta(days=promised_days)
        status = rng.choices(["Delivered", "In Transit", "Cancelled"], [.92, .05, .03])[0]
        order_id = f"O{i:05}"
        warehouse = warehouses[rng.randrange(len(warehouses))]
        orders.append({
            "order_id": order_id, "order_date": order_date.isoformat(),
            "promised_date": promised_date.isoformat(), "customer_region": rng.choice(regions),
            "warehouse_id": warehouse["warehouse_id"], "order_status": status,
        })
        total_units = 0
        for line_number, product in enumerate(rng.sample(products, rng.randint(1, 4)), 1):
            quantity = rng.randint(2, 60)
            total_units += quantity
            lines.append({"order_id": order_id, "line_number": line_number,
                          "product_id": product["product_id"], "quantity": quantity})

        if status == "Cancelled":
            shipment = {"shipment_id": f"SH{i:05}", "order_id": order_id, "ship_date": "",
                        "delivery_date": "", "carrier": "", "shipping_cost": "", "damaged_units": 0}
        else:
            ship_date = order_date + timedelta(days=rng.randint(1, 3))
            delay_bias = 2 if warehouse["warehouse_id"] == "W003" else 0
            transit = max(1, int(rng.gauss(4 + delay_bias, 2)))
            delivery_date = ship_date + timedelta(days=transit) if status == "Delivered" else None
            damage_rate = .025 if warehouse["warehouse_id"] == "W003" else .010
            shipment = {
                "shipment_id": f"SH{i:05}", "order_id": order_id, "ship_date": ship_date.isoformat(),
                "delivery_date": delivery_date.isoformat() if delivery_date else "",
                "carrier": rng.choice(carriers), "shipping_cost": round(12 + total_units * rng.uniform(.45, 1.15), 2),
                "damaged_units": sum(rng.random() < damage_rate for _ in range(total_units)),
            }
        shipments.append(shipment)

    return {"suppliers": suppliers, "warehouses": warehouses, "products": products,
            "orders": orders, "order_lines": lines, "shipments": shipments}


def validate(data: dict[str, list[dict]]) -> None:
    assert len({row["order_id"] for row in data["orders"]}) == len(data["orders"])
    assert all(float(row["unit_price"]) > float(row["unit_cost"]) for row in data["products"])
    order_ids = {row["order_id"] for row in data["orders"]}
    assert all(row["order_id"] in order_ids for row in data["order_lines"])
    assert all(row["order_id"] in order_ids for row in data["shipments"])
    assert all(int(row["damaged_units"]) >= 0 for row in data["shipments"])


def build_database(data: dict[str, list[dict]]) -> None:
    DATA.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table, rows in data.items():
            columns = list(rows[0])
            placeholders = ", ".join("?" for _ in columns)
            connection.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                [[None if value == "" else value for value in row.values()] for row in rows],
            )


def export_dashboard_views() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    queries = {
        "order_performance": """
            SELECT o.*, sh.ship_date, sh.delivery_date, sh.carrier, sh.shipping_cost,
                   sh.damaged_units,
                   CASE WHEN o.order_status='Delivered' AND sh.delivery_date<=o.promised_date THEN 1 ELSE 0 END AS on_time_flag,
                   CASE WHEN o.order_status='Delivered' THEN julianday(sh.delivery_date)-julianday(o.order_date) END AS cycle_days
            FROM orders o LEFT JOIN shipments sh USING(order_id)""",
        "line_detail": """
            SELECT ol.*, o.order_date, o.promised_date, o.customer_region, o.warehouse_id,
                   o.order_status, p.product_name, p.category, p.supplier_id,
                   p.unit_cost, p.unit_price, ol.quantity*p.unit_price AS revenue
            FROM order_lines ol JOIN orders o USING(order_id) JOIN products p USING(product_id)""",
    }
    with sqlite3.connect(DB_PATH) as connection:
        for name, query in queries.items():
            cursor = connection.execute(query)
            with (PROCESSED / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([column[0] for column in cursor.description])
                writer.writerows(cursor)


def main() -> None:
    data = generate_data()
    validate(data)
    for name, rows in data.items():
        write_csv(name, rows)
    build_database(data)
    export_dashboard_views()
    print(f"Built {DB_PATH} with {len(data['orders']):,} orders.")
    print(f"Dashboard exports written to {PROCESSED}.")


if __name__ == "__main__":
    main()

