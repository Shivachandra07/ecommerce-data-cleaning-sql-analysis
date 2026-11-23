# E-Commerce Customer & Order Data Cleaning and SQL Analysis

A Python + SQL project that takes raw customer and order exports, cleans and standardises them, loads them into a relational database with primary/foreign key constraints, answers business questions with SQL, and exports the results to Excel.

```
raw CSVs  ──▶  Python cleaning  ──▶  database (PK/FK)  ──▶  SQL analysis  ──▶  Excel workbook
customers     dates, currency,        referential           joins, CTEs,      output/
orders        duplicates, emails      integrity             window functions  business_summary.xlsx
```

## The raw data problems it fixes

| Problem | Fix |
| --- | --- |
| Duplicate customer and order rows | de-duplicated on `customer_id` / `order_id` |
| Names in `ALL CAPS`, lowercase, padded with spaces | trimmed and title-cased |
| Blank or malformed emails (`test@`, `shiva@@example.com`) | validated with a regex, invalid rows removed |
| Dates in `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-Mon-YYYY`, `Mon DD, YYYY` | parsed to one ISO format |
| Prices like `$1,299.00` | converted to numeric |
| `Completed`, `COMPLETE`, `completed` | mapped to `completed` |
| Orders pointing at a non-existent customer | removed (referential integrity) |
| Quantity `0`, `-2`, `two`; price `N/A` | removed |

Every removed row is **counted** in `logs/cleaning_report.txt`, so nothing disappears silently.

## Database schema

```mermaid
erDiagram
    customers ||--o{ orders : places

    customers {
        text customer_id PK
        text full_name
        text email UK
        text city
        text country
        text signup_date
    }
    orders {
        text order_id PK
        text customer_id FK
        text order_date
        text product_name
        text category
        int quantity
        numeric unit_price
        numeric total_amount
        text status
    }
```

Constraints enforced by the database: primary keys, a unique email, `quantity > 0`, `unit_price >= 0`, and `orders.customer_id → customers.customer_id`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/generate_sample_data.py   # sample raw data is already included
python cleaning/clean_data.py            # writes data/cleaned/*.csv + cleaning report
python load_to_db.py                     # creates schema and loads the database
python export_reports.py                 # writes output/business_summary.xlsx
```

There is also `cleaning/cleaning_walkthrough.ipynb`, a step-by-step notebook showing the raw data, the problems and each cleaning step.

By default everything runs on a local SQLite database (`data/ecommerce.db`), so **no database installation is required**. To use PostgreSQL:

```bash
createdb ecommerce_db
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/ecommerce_db"
python load_to_db.py
python export_reports.py
```

## Business questions answered (`sql/analysis_queries.sql`)

1. Monthly revenue trend
2. Top 10 products by revenue and units sold
3. Repeat vs one-time customers — revenue and average lifetime value (CTE)
4. Repeat customer retention rate
5. Top 10 customers by lifetime value (`RANK()` window function)
6. Month-over-month revenue growth (`LAG()` window function, with `NULLIF` guard)
7. Revenue by country (join + aggregation)
8. Category mix as a share of total revenue (window function over a CTE)
9. Average order value per month

## Excel output

`python export_reports.py` builds `output/business_summary.xlsx` with a **Cleaning Summary** sheet plus one sheet per query, so the SQL results can be shared with non-technical stakeholders.

## Repository layout

```
ecommerce-data-cleaning-sql-analysis/
├── cleaning/
│   ├── clean_data.py                # cleaning functions + report
│   └── cleaning_walkthrough.ipynb   # step-by-step notebook
├── scripts/generate_sample_data.py  # creates deliberately messy raw CSVs
├── sql/
│   ├── schema_postgres.sql
│   ├── schema_sqlite.sql
│   └── analysis_queries.sql
├── load_to_db.py                    # clean → create schema (PK/FK) → load
├── export_reports.py                # SQL → Excel workbook
├── db.py                            # PostgreSQL or SQLite engine
└── data/raw/{customers,orders}_raw.csv
```

## Notes

- Sample data uses a fixed random seed, so results are reproducible.
- Query results in the Excel export are the live output of the SQL file — edit a query, rerun, and the workbook updates.
