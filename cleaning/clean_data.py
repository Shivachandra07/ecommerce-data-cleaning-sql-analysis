"""Clean the raw e-commerce customer and order exports.

Every fix is counted and written to logs/cleaning_report.txt so the cleaning
is auditable instead of being a black box.

Run from the project root:
    python cleaning/clean_data.py
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEANED_DIR = ROOT / "data" / "cleaned"
LOG_DIR = ROOT / "logs"

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y", "%b %d, %Y")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
STATUS_MAP = {
    "complete": "completed",
    "completed": "completed",
    "shipped": "shipped",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "returned": "returned",
}

logger = logging.getLogger(__name__)


def parse_date(value) -> pd.Timestamp:
    if value is None:
        return pd.NaT
    text = str(value).strip()
    if not text:
        return pd.NaT
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(text, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(text, errors="coerce", dayfirst=True)


def parse_money(value) -> float:
    if value is None:
        return float("nan")
    text = str(value).strip()
    if not text:
        return float("nan")
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    try:
        return float(cleaned)
    except ValueError:
        return float("nan")


def clean_customers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    issues: dict[str, int] = {}
    customers = df.copy()
    raw_rows = len(customers)

    customers.columns = [c.strip().lower() for c in customers.columns]
    for column in ["customer_id", "full_name", "email", "city", "country", "signup_date"]:
        customers[column] = customers[column].astype(str).str.strip()

    customers["customer_id"] = customers["customer_id"].str.upper()
    customers["full_name"] = customers["full_name"].str.replace(r"\s+", " ", regex=True).str.title()
    customers["email"] = customers["email"].str.lower()
    customers["city"] = customers["city"].str.title()
    customers["country"] = customers["country"].str.title()
    customers["signup_date"] = customers["signup_date"].map(parse_date)
    customers["signup_date"] = customers["signup_date"].dt.strftime("%Y-%m-%d")

    before = len(customers)
    customers = customers[customers["customer_id"].ne("") & customers["full_name"].ne("")]
    issues["missing_id_or_name_removed"] = before - len(customers)

    before = len(customers)
    valid_email = customers["email"].str.match(EMAIL_PATTERN)
    issues["invalid_email_removed"] = int((~valid_email).sum())
    customers = customers[valid_email]

    before = len(customers)
    customers = customers.drop_duplicates(subset=["customer_id"], keep="last")
    issues["duplicate_customers_removed"] = before - len(customers)

    issue_signup = int(customers["signup_date"].isna().sum())
    issues["missing_signup_dates"] = issue_signup

    customers = customers.sort_values("customer_id").reset_index(drop=True)
    issues["rows_before"] = raw_rows
    issues["rows_after"] = len(customers)
    logger.info("Customers cleaned: %s -> %s rows", raw_rows, len(customers))
    return customers, issues


def clean_orders(df: pd.DataFrame, valid_customer_ids: pd.Series) -> tuple[pd.DataFrame, dict]:
    issues: dict[str, int] = {}
    orders = df.copy()
    raw_rows = len(orders)

    orders.columns = [c.strip().lower() for c in orders.columns]
    for column in orders.columns:
        orders[column] = orders[column].astype(str).str.strip()

    orders["order_id"] = orders["order_id"].str.upper()
    orders["customer_id"] = orders["customer_id"].str.upper()
    orders["product_name"] = orders["product_name"].str.title()
    orders["category"] = orders["category"].str.title()
    orders["order_date"] = orders["order_date"].map(parse_date)
    orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
    orders["unit_price"] = orders["unit_price"].map(parse_money)
    orders["status"] = (
        orders["status"].str.lower().str.replace(r"[^a-z]", "", regex=True).map(STATUS_MAP)
    )

    before = len(orders)
    orders = orders.drop_duplicates(subset=["order_id"], keep="first")
    issues["duplicate_orders_removed"] = before - len(orders)

    before = len(orders)
    valid_customers = set(valid_customer_ids)
    orders = orders[orders["customer_id"].isin(valid_customers)]
    issues["orphan_orders_removed"] = before - len(orders)

    before = len(orders)
    valid_rows = (
        orders["order_date"].notna()
        & (orders["quantity"] > 0)
        & (orders["unit_price"] >= 0)
        & orders["status"].notna()
    )
    issues["invalid_values_removed"] = int((~valid_rows).sum())
    orders = orders[valid_rows].copy()

    orders["quantity"] = orders["quantity"].astype(int)
    orders["order_date"] = orders["order_date"].dt.strftime("%Y-%m-%d")
    orders["total_amount"] = (orders["quantity"] * orders["unit_price"]).round(2)

    orders = orders.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    issues["rows_before"] = raw_rows
    issues["rows_after"] = len(orders)
    logger.info("Orders cleaned: %s -> %s rows", raw_rows, len(orders))
    return orders, issues


def write_report(customer_issues: dict, order_issues: dict) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "E-commerce data cleaning report",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "CUSTOMERS",
        f"  rows read              : {customer_issues['rows_before']:,}",
        f"  duplicate customers    : {customer_issues['duplicate_customers_removed']:,}",
        f"  invalid emails removed : {customer_issues['invalid_email_removed']:,}",
        f"  missing id/name removed: {customer_issues['missing_id_or_name_removed']:,}",
        f"  missing signup dates   : {customer_issues['missing_signup_dates']:,}",
        f"  rows written           : {customer_issues['rows_after']:,}",
        "",
        "ORDERS",
        f"  rows read              : {order_issues['rows_before']:,}",
        f"  duplicate orders       : {order_issues['duplicate_orders_removed']:,}",
        f"  orphan orders removed  : {order_issues['orphan_orders_removed']:,}",
        f"  invalid values removed : {order_issues['invalid_values_removed']:,}",
        f"  rows written           : {order_issues['rows_after']:,}",
    ]
    path = LOG_DIR / "cleaning_report.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    customers = pd.read_csv(RAW_DIR / "customers_raw.csv", dtype=str, keep_default_na=False)
    orders = pd.read_csv(RAW_DIR / "orders_raw.csv", dtype=str, keep_default_na=False)
    return customers, orders


def clean_all() -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    customers_raw, orders_raw = load_raw()
    customers, customer_issues = clean_customers(customers_raw)
    orders, order_issues = clean_orders(orders_raw, customers["customer_id"])
    return customers, orders, customer_issues, order_issues


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s", datefmt="%H:%M:%S")
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    customers, orders, customer_issues, order_issues = clean_all()
    customers.to_csv(CLEANED_DIR / "customers_clean.csv", index=False)
    orders.to_csv(CLEANED_DIR / "orders_clean.csv", index=False)
    path = write_report(customer_issues, order_issues)
    print(f"Wrote {len(customers):,} customers and {len(orders):,} orders")
    print(f"Cleaning report: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
