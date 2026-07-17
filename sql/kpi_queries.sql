-- Executive KPIs
SELECT
    COUNT(*) AS total_orders,
    ROUND(100.0 * SUM(order_status = 'Delivered') / COUNT(*), 1) AS fulfillment_rate_pct,
    ROUND(100.0 * SUM(
        order_status = 'Delivered' AND delivery_date <= promised_date
    ) / NULLIF(SUM(order_status = 'Delivered'), 0), 1) AS on_time_delivery_pct,
    ROUND(AVG(CASE WHEN order_status = 'Delivered'
        THEN julianday(delivery_date) - julianday(order_date) END), 1) AS avg_cycle_time_days,
    ROUND(SUM(COALESCE(shipping_cost, 0)), 2) AS total_shipping_cost
FROM orders
LEFT JOIN shipments USING (order_id);

-- Supplier scorecard
SELECT
    s.supplier_id,
    s.supplier_name,
    COUNT(DISTINCT o.order_id) AS delivered_orders,
    ROUND(100.0 * AVG(sh.delivery_date <= o.promised_date), 1) AS on_time_pct,
    ROUND(100.0 * SUM(sh.damaged_units) / NULLIF(SUM(ol.quantity), 0), 2) AS damage_rate_pct,
    ROUND(SUM(ol.quantity * p.unit_cost), 2) AS purchase_value
FROM suppliers s
JOIN products p USING (supplier_id)
JOIN order_lines ol USING (product_id)
JOIN orders o USING (order_id)
JOIN shipments sh USING (order_id)
WHERE o.order_status = 'Delivered'
GROUP BY s.supplier_id, s.supplier_name
ORDER BY on_time_pct, damage_rate_pct DESC;

-- Warehouse performance
SELECT
    w.warehouse_name,
    COUNT(*) AS orders,
    ROUND(100.0 * AVG(CASE WHEN o.order_status = 'Delivered'
        THEN sh.delivery_date <= o.promised_date END), 1) AS on_time_pct,
    ROUND(AVG(sh.shipping_cost), 2) AS avg_shipping_cost,
    ROUND(AVG(CASE WHEN o.order_status = 'Delivered'
        THEN julianday(sh.delivery_date) - julianday(o.order_date) END), 1) AS avg_cycle_days
FROM warehouses w
JOIN orders o USING (warehouse_id)
LEFT JOIN shipments sh USING (order_id)
GROUP BY w.warehouse_id, w.warehouse_name
ORDER BY on_time_pct;

-- Monthly trend
SELECT
    substr(o.order_date, 1, 7) AS month,
    COUNT(*) AS orders,
    ROUND(SUM(ol.quantity * p.unit_price), 2) AS gross_revenue,
    ROUND(100.0 * AVG(CASE WHEN o.order_status = 'Delivered'
        THEN sh.delivery_date <= o.promised_date END), 1) AS on_time_pct,
    ROUND(SUM(COALESCE(sh.shipping_cost, 0)), 2) AS shipping_cost
FROM orders o
JOIN order_lines ol USING (order_id)
JOIN products p USING (product_id)
LEFT JOIN shipments sh USING (order_id)
GROUP BY month
ORDER BY month;

