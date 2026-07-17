# Data dictionary

## Core warehouse tables

| Table | Grain | Purpose |
|---|---|---|
| `suppliers` | One row per supplier | Supplier region, contracted lead time, and quality target |
| `products` | One row per SKU | Product category, supplier, cost, price, and reorder point |
| `warehouses` | One row per distribution center | Location and unit capacity |
| `orders` | One row per customer order | Order dates, promise date, region, warehouse, and status |
| `order_lines` | One row per order-SKU line | Quantity and product detail bridge |
| `shipments` | One row per order | Carrier, shipping cost, delivery date, and damaged units |
| `inventory_snapshots` | One row per date-warehouse-SKU | On-hand, allocated, inbound, and average daily demand |

## Derived operational fields

| Field | Definition |
|---|---|
| `on_time_flag` | 1 when a delivered order arrives on or before its promised date |
| `cycle_days` | Calendar days between order and delivery |
| `available_units` | On-hand units minus allocated units |
| `days_of_supply` | Available units divided by average daily demand |
| `estimated_margin_exposure` | Expected gross margin exposed during the lead-time coverage gap |
| `priority` | P1 stockout/critical, P2 expedite, or P3 monitor |

## Assumptions

- Dates are stored as ISO `YYYY-MM-DD` strings for SQLite portability.
- Monetary values are synthetic U.S. dollars.
- Average daily demand is a deterministic simulated planning input.
- Margin exposure is a prioritization estimate, not an accounting forecast.
- The intervention scenario changes delivery timing only and does not claim causal proof.

