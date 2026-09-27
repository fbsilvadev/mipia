"""Creates orders.db with fictional sample data (no real customers)."""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB = Path(__file__).with_name("orders.db")
random.seed(7)

CUSTOMERS = ["Northwind Traders", "Alder & Finch", "Kestrel Labs", "Brightwater Co", "Oakline Studio", "Harbor Point Ltd"]
PRODUCTS = [("KB-100", "Mechanical keyboard", 89.0), ("MS-220", "Wireless mouse", 39.5),
            ("HD-330", "USB-C hub", 54.9), ("MN-440", "27in monitor", 259.0), ("CB-050", "Cable kit", 14.9)]
STATUSES = ["paid", "shipped", "shipped", "shipped", "cancelled", "refunded"]

if DB.exists():
    DB.unlink()
conn = sqlite3.connect(DB)
conn.executescript("""
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT NOT NULL, status TEXT NOT NULL, order_date TEXT NOT NULL, total REAL NOT NULL);
CREATE TABLE order_items (order_id INTEGER NOT NULL REFERENCES orders(id), sku TEXT NOT NULL, name TEXT NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL);
""")
start = date(2026, 1, 1)
for oid in range(1, 121):
    d = start + timedelta(days=random.randint(0, 250))
    items = random.sample(PRODUCTS, random.randint(1, 3))
    lines = [(sku, name, random.randint(1, 4), price) for sku, name, price in items]
    total = round(sum(q * p for _, _, q, p in lines), 2)
    conn.execute("INSERT INTO orders VALUES (?,?,?,?,?)", (oid, random.choice(CUSTOMERS), random.choice(STATUSES), d.isoformat(), total))
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", [(oid, *l) for l in lines])
conn.commit()
print("orders.db created with 120 orders")
