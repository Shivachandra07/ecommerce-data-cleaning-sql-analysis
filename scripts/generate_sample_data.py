"""Generate messy e-commerce customer and order CSVs.

The raw files copy the kinds of problems real exports have: duplicated rows,
missing values, inconsistent capitalisation, mixed date formats, currency
symbols, invalid emails and orders that point to customers who do not exist.

Run from the project root:
    python scripts/generate_sample_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

FIRST_NAMES = [
    "Shivachandra", "Ananya", "Rahul", "Priya", "Kiran", "Meera", "Arjun", "Sneha",
    "Vikram", "Divya", "Rohit", "Kavya", "Aditya", "Nisha", "Sai", "Lakshmi",
    "Manoj", "Pooja", "Harsha", "Ravi", "Deepa", "Ajay", "Swathi", "Naveen",
    "Chaitra", "Suresh", "Anjali", "Vamsi", "Harini", "Karthik",
]
LAST_NAMES = [
    "Reddy", "Sharma", "Kumar", "Patel", "Rao", "Naidu", "Iyer", "Gupta",
    "Verma", "Chowdhary", "Nair", "Menon", "Shetty", "Joshi", "Desai",
]
CITIES = [
    ("Hyderabad", "India"),
    ("Bengaluru", "India"),
    ("Chennai", "India"),
    ("Vijayawada", "India"),
    ("Mumbai", "India"),
    ("Pune", "India"),
    ("Delhi", "India"),
    ("Singapore", "Singapore"),
    ("Dubai", "UAE"),
    ("London", "UK"),
]
PRODUCTS = [
    ("Bluetooth Earbuds", "Electronics", 49.99),
    ("Smart Watch", "Electronics", 129.00),
    ("Laptop Stand", "Electronics", 34.50),
    ("Phone Case", "Electronics", 15.99),
    ("Cotton Kurta", "Fashion", 39.00),
    ("Running Shoes", "Fashion", 79.99),
    ("Leather Wallet", "Fashion", 29.50),
    ("Sunglasses", "Fashion", 59.00),
    ("Coffee Mug", "Home", 12.99),
    ("Bedsheet Set", "Home", 44.00),
    ("Table Lamp", "Home", 27.50),
    ("Kitchen Knife Set", "Home", 89.00),
    ("Yoga Mat", "Sports", 25.00),
    ("Cricket Bat", "Sports", 115.00),
    ("Protein Shaker", "Sports", 18.99),
    ("Gaming Mouse", "Electronics", 42.00),
]
STATUSES = ["completed", "Completed", "COMPLETE", "shipped", "cancelled", "Cancelled", "returned"]


def messy_date(d: date) -> str:
    choice = random.random()
    if choice < 0.5:
        return d.isoformat()
    if choice < 0.75:
        return d.strftime("%d/%m/%Y")
    if choice < 0.9:
        return d.strftime("%d-%b-%Y")
    return d.strftime("%b %d, %Y")


def messy_money(value: float) -> str:
    choice = random.random()
    if choice < 0.12:
        return f"${value:,.2f}"
    if choice < 0.2:
        return f"{value:,.2f}"
    return f"{value:.2f}"


def messy_name(first: str, last: str) -> str:
    choice = random.random()
    full = f"{first} {last}"
    if choice < 0.12:
        return full.upper()
    if choice < 0.24:
        return full.lower()
    if choice < 0.34:
        return f"  {full}  "
    return full


def messy_email(first: str, last: str, number: int) -> str:
    choice = random.random()
    base = f"{first.lower()}.{last.lower()}{number}@example.com"
    if choice < 0.1:
        return base.upper()
    if choice < 0.18:
        return f"  {base} "
    return base


def build_customers(count: int = 320) -> list[list[str]]:
    random.seed(7)
    customers: list[list[str]] = []
    start = date(2022, 1, 1)

    for number in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        city, country = random.choice(CITIES)
        signup = start + timedelta(days=random.randint(0, 900))
        city_text, country_text = city, country
        if random.random() < 0.15:
            city_text = city.upper()
        if random.random() < 0.15:
            country_text = country.lower()
        customers.append(
            [
                f"C{number:04d}",
                messy_name(first, last),
                messy_email(first, last, number),
                city_text,
                country_text,
                messy_date(signup),
            ]
        )

    # Problems: duplicate customers, missing emails, invalid emails, blank names
    for _ in range(15):
        customers.append(list(random.choice(customers)))
    for index in random.sample(range(len(customers)), 12):
        customers[index][2] = ""
    for index in random.sample(range(len(customers)), 8):
        customers[index][2] = random.choice(["not-an-email", "shiva@@example.com", "test@", "  "])
    for index in random.sample(range(len(customers)), 5):
        customers[index][1] = ""

    random.shuffle(customers)
    return customers


def build_orders(customers: list[list[str]], count: int = 1600) -> list[list[str]]:
    random.seed(11)
    customer_ids = [row[0] for row in customers if row[0].strip()]
    orders: list[list[str]] = []
    start = date(2023, 1, 1)

    for number in range(1, count + 1):
        order_id = f"O{number:05d}"
        order_day = start + timedelta(days=random.randint(0, 729))
        product, category, price = random.choice(PRODUCTS)
        quantity = random.choices([1, 1, 1, 2, 2, 3], k=1)[0]
        orders.append(
            [
                order_id,
                random.choice(customer_ids),
                messy_date(order_day),
                product,
                category,
                str(quantity),
                messy_money(price),
                random.choice(STATUSES),
            ]
        )

    # Problems: duplicate order rows, missing customer, unknown customer,
    # bad quantities, bad prices and blank dates.
    for _ in range(45):
        orders.append(list(random.choice(orders)))
    for index in random.sample(range(len(orders)), 25):
        orders[index][1] = ""
    for index in random.sample(range(len(orders)), 15):
        orders[index][1] = f"C9{random.randint(100, 999)}"  # never existed
    for index in random.sample(range(len(orders)), 10):
        orders[index][5] = random.choice(["0", "-2", "two"])
    for index in random.sample(range(len(orders)), 8):
        orders[index][6] = random.choice(["", "N/A"])
    for index in random.sample(range(len(orders)), 10):
        orders[index][2] = ""

    random.shuffle(orders)
    return orders


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    customers = build_customers()
    orders = build_orders(customers)

    with (RAW_DIR / "customers_raw.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["customer_id", "full_name", "email", "city", "country", "signup_date"])
        writer.writerows(customers)

    with (RAW_DIR / "orders_raw.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["order_id", "customer_id", "order_date", "product_name", "category", "quantity", "unit_price", "status"]
        )
        writer.writerows(orders)

    print(f"Wrote {len(customers):,} raw customers and {len(orders):,} raw orders")


if __name__ == "__main__":
    main()
