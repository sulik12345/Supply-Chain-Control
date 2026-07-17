# Executive Supply Chain Brief

Generated from the reproducible control-tower dataset.

![Control tower preview](dashboard_preview.svg)

## Decision summary

- Network on-time delivery is 68.0%; West Coast DC is the constraint at 54.3%.
- A two-day West Coast transit improvement raises local on-time service to 78.8%, adding 135 on-time orders.
- The exception queue ranks 10 immediate actions by estimated gross-margin exposure.

## Warehouse performance

| warehouse | orders | on_time_pct | avg_ship_cost | cycle_days |
| --- | --- | --- | --- | --- |
| West Coast DC | 599 | 54.3 | 73.53 | 7.4 |
| Central DC | 593 | 74.2 | 73.62 | 5.6 |
| East Coast DC | 608 | 75.4 | 75.99 | 5.5 |

## Lowest-performing warehouse/carrier lanes

| warehouse | carrier | orders | on_time_pct | transit_days | avg_ship_cost |
| --- | --- | --- | --- | --- | --- |
| West Coast DC | SwiftFreight | 150 | 48.7 | 5.5 | 75.19 |
| West Coast DC | RoadRunner | 130 | 54.6 | 5.4 | 76.08 |
| West Coast DC | National Logistics | 134 | 55.2 | 5.3 | 76.85 |
| West Coast DC | ParcelPro | 137 | 59.1 | 5.4 | 69.67 |
| Central DC | SwiftFreight | 128 | 68.8 | 3.7 | 79.5 |
| East Coast DC | ParcelPro | 147 | 70.7 | 3.6 | 72.61 |
| Central DC | ParcelPro | 133 | 72.2 | 3.8 | 76.65 |
| East Coast DC | RoadRunner | 141 | 74.5 | 3.6 | 77.76 |

## Priority exception queue

| warehouse | product_id | product | days_supply | lead_time | daily_margin_risk | margin_exposure | priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Central DC | P003 | Industrial Item 03 | 3.0 | 14 | 1902.35 | 20895.63 | P1 Critical |
| East Coast DC | P027 | Office Item 27 | 1.6 | 14 | 1150.2 | 14319.99 | P1 Critical |
| East Coast DC | P014 | Safety Item 14 | 0.6 | 11 | 1289.78 | 13445.69 | P1 Critical |
| East Coast DC | P022 | Office Item 22 | 0.1 | 7 | 1447.07 | 10055.65 | P1 Critical |
| Central DC | P027 | Office Item 27 | 6.1 | 14 | 966.17 | 7660.33 | P1 Critical |
| Central DC | P011 | Electronics Item 11 | 0.0 | 10 | 755.8 | 7558.0 | P1 Stockout |
| East Coast DC | P003 | Industrial Item 03 | 9.8 | 14 | 1683.43 | 7111.16 | P2 Expedite |
| East Coast DC | P008 | Industrial Item 08 | 0.0 | 11 | 612.93 | 6742.2 | P1 Stockout |
| Central DC | P016 | Electronics Item 16 | 1.1 | 7 | 1045.7 | 6209.43 | P1 Critical |
| Central DC | P019 | Safety Item 19 | 4.6 | 8 | 1717.94 | 5861.19 | P1 Critical |

## Two-day transit improvement scenario

| metric | value |
| --- | --- |
| delivered_orders | 551 |
| baseline_on_time_pct | 54.3 |
| scenario_on_time_pct | 78.8 |
| additional_on_time_orders | 135 |
| service_lift_points | 24.5 |
| delivered_margin | 1684482.57 |

## Recommended actions

1. Pilot carrier and fulfillment interventions at West Coast DC.
2. Expedite the highest margin-exposure inventory exceptions first.
3. Review the carrier-lane scorecard weekly rather than relying on network averages.
4. Measure the pilot against the documented baseline before scaling.
