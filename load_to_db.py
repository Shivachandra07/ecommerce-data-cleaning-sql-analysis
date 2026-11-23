"""Clean the raw CSVs and load them into the database with keys and constraints.

    python load_to_db.py

Writes to data/ecommerce.db (SQLite) unless DATABASE_URL points at PostgreSQL.
"""

from __future__ import annotations

import argparse
import logging

import pandas as pd

from cleaning.clean_data import CLEANED_DIR, clean_all, write_report
from db import get_engine, reset_schema


def main() -> None:
    parser = argparse.ArgumentParser(description="Load cleaned e-commerce data into the database")
    parser.add_argument("--database-url", help="override DATABASE_URL for this run")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")

    customers, orders, customer_issues, order_issues = clean_all()
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    customers.to_csv(CLEANED_DIR / "customers_clean.csv", index=False)
    orders.to_csv(CLEANED_DIR / "orders_clean.csv", index=False)
    report_path = write_report(customer_issues, order_issues)
    print(f"Cleaning report: {report_path}")

    engine = get_engine(args.database_url)
    reset_schema(engine)

    with engine.begin() as connection:
        # Customers first: orders have a foreign key pointing at them.
        customers.to_sql("customers", connection, if_exists="append", index=False)
        orders.to_sql("orders", connection, if_exists="append", index=False)

    with engine.connect() as connection:
        customer_count = pd.read_sql("SELECT COUNT(*) AS n FROM customers", connection)["n"][0]
        order_count = pd.read_sql("SELECT COUNT(*) AS n FROM orders", connection)["n"][0]

    print(f"Loaded {customer_count:,} customers and {order_count:,} orders")
    print(f"Database: {engine.url.render_as_string(hide_password=True)}")


if __name__ == "__main__":
    main()
