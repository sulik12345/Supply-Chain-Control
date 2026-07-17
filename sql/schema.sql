PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS inventory_snapshots;
DROP TABLE IF EXISTS order_lines;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS warehouses;

CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    region TEXT NOT NULL,
    contracted_lead_time_days INTEGER NOT NULL CHECK (contracted_lead_time_days > 0),
    quality_target REAL NOT NULL CHECK (quality_target BETWEEN 0 AND 1)
);

CREATE TABLE warehouses (
    warehouse_id TEXT PRIMARY KEY,
    warehouse_name TEXT NOT NULL,
    state TEXT NOT NULL,
    capacity_units INTEGER NOT NULL CHECK (capacity_units > 0)
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
    unit_cost REAL NOT NULL CHECK (unit_cost > 0),
    unit_price REAL NOT NULL CHECK (unit_price > unit_cost),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0)
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    customer_region TEXT NOT NULL,
    warehouse_id TEXT NOT NULL REFERENCES warehouses(warehouse_id),
    order_status TEXT NOT NULL CHECK (order_status IN ('Delivered', 'In Transit', 'Cancelled'))
);

CREATE TABLE order_lines (
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    line_number INTEGER NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, line_number)
);

CREATE TABLE shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE REFERENCES orders(order_id),
    ship_date TEXT,
    delivery_date TEXT,
    carrier TEXT,
    shipping_cost REAL CHECK (shipping_cost >= 0),
    damaged_units INTEGER NOT NULL DEFAULT 0 CHECK (damaged_units >= 0)
);

CREATE TABLE inventory_snapshots (
    snapshot_date TEXT NOT NULL,
    warehouse_id TEXT NOT NULL REFERENCES warehouses(warehouse_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    on_hand_units INTEGER NOT NULL CHECK (on_hand_units >= 0),
    allocated_units INTEGER NOT NULL CHECK (allocated_units >= 0),
    inbound_units INTEGER NOT NULL CHECK (inbound_units >= 0),
    avg_daily_demand REAL NOT NULL CHECK (avg_daily_demand >= 0),
    PRIMARY KEY (snapshot_date, warehouse_id, product_id)
);

CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_warehouse ON orders(warehouse_id);
CREATE INDEX idx_order_lines_product ON order_lines(product_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_inventory_product ON inventory_snapshots(product_id);
