# Executive Supply Chain Brief

Generated from the reproducible control-tower dataset.

## Network KPIs

| orders | fulfillment_pct | on_time_pct | cycle_days | shipping_cost |
| --- | --- | --- | --- | --- |
| 1800 | 92.4 | 68.0 | 6.2 | 130636.0 |

## Key findings

- The network delivered **68.0%** of completed orders on time.
- **West Coast DC** is the primary service-risk location at **54.3%** on-time delivery and a **7.4-day** average cycle.
- The latest inventory snapshot contains **34 critical SKUs** with fewer than seven available days of supply.
- Prioritize West Coast carrier and process review, then expedite inbound inventory for critical SKUs before increasing broad safety stock.

## Warehouse performance

| warehouse | orders | on_time_pct | avg_ship_cost | cycle_days |
| --- | --- | --- | --- | --- |
| West Coast DC | 599 | 54.3 | 73.53 | 7.4 |
| Central DC | 593 | 74.2 | 73.62 | 5.6 |
| East Coast DC | 608 | 75.4 | 75.99 | 5.5 |

## Inventory exposure

| warehouse | critical_skus | avg_days_supply |
| --- | --- | --- |
| Central DC | 13 | 11.4 |
| East Coast DC | 11 | 9.4 |
| West Coast DC | 10 | 12.9 |

## Recommended actions

1. Review West Coast DC pick/pack time and carrier transit performance.
2. Create daily alerts for SKUs below seven days of available supply.
3. Track on-time delivery and damage rate by warehouse-carrier pair.
4. Validate improvements against the current network baseline.
