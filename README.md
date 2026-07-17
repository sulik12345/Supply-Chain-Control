# Supply Chain Control Tower

An end-to-end analytics project that turns fragmented order, supplier, product, warehouse, and shipment data into operational KPIs and decision-ready datasets.

## Business problem

Leadership needs one reliable view of fulfillment performance. Orders are growing, but late deliveries, damage, and transportation costs vary across warehouses and suppliers. This project builds a reproducible control-tower data layer to answer:

- Are customers receiving orders on time?
- Which suppliers and warehouses create the most operational risk?
- Where are shipping costs and cycle times increasing?
- Which products and regions drive revenue and service failures?

## Solution

```text
Synthetic operational data
        |
        v
Data validation -> SQLite warehouse -> SQL KPI layer -> Dashboard-ready CSVs
```

The deterministic generator creates a full year of realistic operational data, including intentionally uneven warehouse performance so the analysis reveals actionable patterns.

## Technology

- Python: reproducible data generation, validation, ETL, and exports
- SQL/SQLite: relational model and analytical queries
- Power BI/Tableau-ready CSV outputs
- `unittest`: pipeline and data-integrity checks

## Data model

```text
suppliers 1---* products 1---* order_lines *---1 orders 1---1 shipments
                                                     *
                                                     |
                                                     1
                                                warehouses
```

## KPIs

- Fulfillment rate
- On-time delivery rate
- Order cycle time
- Shipping cost per order
- Supplier damage rate
- Purchase value by supplier
- Warehouse and monthly performance trends

## Run locally

Requires Python 3.10 or newer. No third-party packages are required.

```bash
python src/pipeline.py
python -m unittest discover -s tests -v
```

The pipeline creates:

- `data/control_tower.db`: analytics-ready SQLite database
- `data/raw/`: normalized source CSVs
- `data/processed/order_performance.csv`: order-level dashboard table
- `data/processed/line_detail.csv`: product and revenue dashboard table

Run the queries in `sql/kpi_queries.sql` against the database or connect Power BI/Tableau to the processed CSV files.

## Repository structure

```text
data/                 Generated locally
sql/schema.sql        Relational warehouse definition
sql/kpi_queries.sql   Executive and operational analysis
src/pipeline.py       Generation, validation, ETL, and export pipeline
tests/                Automated integrity and KPI tests
```

## Design decisions and limitations

- Synthetic data avoids publishing confidential company information and makes the project fully reproducible.
- SQLite keeps setup simple; the schema can be migrated to PostgreSQL, BigQuery, or Snowflake.
- This first release focuses on the governed analytics layer. A Power BI dashboard and inventory snapshot model are planned next.

## Portfolio takeaway

This project demonstrates the ability to translate a supply-chain problem into a relational model, validate operational data, calculate service and cost KPIs, and prepare trusted outputs for executive reporting.

