"""Regenerate the date-sensitive sample data relative to today.

Lab 3 asks "which items expire within 60 days?" and Lab 9 checks a 14-day
refund window. Fixed dates would go stale during the semester, so this script
writes the two CSV files with dates counted from today. It runs automatically
when the Codespace is created; run it again at any time:

    python scripts/refresh_dates.py
"""
import csv
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = date.today()


def d(days: int) -> str:
    return (TODAY + timedelta(days=days)).isoformat()


# item, strength, form, quantity, unit_price_ghs, days until expiry
PHARMACY = [
    ("Amoxicillin", "500mg", "capsules (pack of 21)", 40, 35.00, 400),
    ("Amoxicillin", "250mg", "capsules (pack of 21)", 12, 22.50, 45),
    ("Paracetamol", "500mg", "tablets (pack of 24)", 150, 8.00, 600),
    ("Paracetamol", "120mg/5ml", "syrup (100ml)", 30, 15.00, 25),
    ("Ibuprofen", "400mg", "tablets (pack of 24)", 60, 12.00, 300),
    ("Artemether-Lumefantrine", "20/120mg", "tablets (pack of 24)", 45, 28.00, 210),
    ("Artemether-Lumefantrine", "80/480mg", "tablets (pack of 6)", 8, 32.00, 55),
    ("Metformin", "500mg", "tablets (pack of 28)", 70, 18.00, 365),
    ("Amlodipine", "5mg", "tablets (pack of 28)", 55, 20.00, 500),
    ("Amlodipine", "10mg", "tablets (pack of 28)", 0, 26.00, 480),
    ("Oral Rehydration Salts", "20.5g", "sachet", 200, 2.50, 30),
    ("Zinc Sulphate", "20mg", "dispersible tablets (pack of 10)", 90, 6.00, 120),
    ("Ciprofloxacin", "500mg", "tablets (pack of 10)", 25, 24.00, 15),
    ("Omeprazole", "20mg", "capsules (pack of 28)", 35, 19.00, 280),
    ("Cetirizine", "10mg", "tablets (pack of 10)", 80, 7.50, 59),
    ("Vitamin C", "500mg", "tablets (pack of 30)", 120, 10.00, 700),
    ("Ferrous Sulphate", "200mg", "tablets (pack of 28)", 65, 9.00, 90),
    ("Folic Acid", "5mg", "tablets (pack of 28)", 50, 6.50, 75),
    ("Salbutamol", "100mcg", "inhaler", 14, 45.00, 160),
    ("Hydrocortisone", "1%", "cream (15g)", 22, 14.00, 5),
]

# order_id, customer (fictional), item, item_price_ghs, delivery_ghs, days ago, refunded
ORDERS = [
    ("KM1001", "Customer A", "Kente stole (small)", 180.00, 25.00, 3, "no"),
    ("KM1002", "Customer B", "Kente cloth (6 yards)", 950.00, 40.00, 5, "no"),
    ("KM1003", "Customer C", "Adinkra print shirt", 220.00, 25.00, 10, "no"),
    ("KM1004", "Customer D", "Kente bag", 260.00, 25.00, 20, "no"),
    ("KM1005", "Customer E", "Kente cloth (12 yards)", 1800.00, 50.00, 2, "no"),
    ("KM1006", "Customer F", "Beaded bracelet set", 75.00, 15.00, 7, "yes"),
    ("KM1007", "Customer G", "Smock (batakari)", 420.00, 30.00, 13, "no"),
    ("KM1008", "Customer H", "Kente bow tie", 90.00, 15.00, 1, "no"),
    ("KM1009", "Customer I", "Kente stole (graduation)", 310.00, 25.00, 15, "no"),
    ("KM1010", "Customer J", "Adinkra stamp set", 140.00, 20.00, 9, "no"),
    ("KM1042", "Customer K", "Kente cloth (6 yards)", 980.00, 40.00, 4, "no"),
]


def write_pharmacy():
    path = ROOT / "lab03" / "data" / "pharmacy_stock.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "strength", "form", "quantity", "unit_price_ghs", "expiry_date"])
        for item, strength, form, qty, price, days in PHARMACY:
            w.writerow([item, strength, form, qty, f"{price:.2f}", d(days)])
    print(f"wrote {path.relative_to(ROOT)} ({len(PHARMACY)} rows)")


def write_orders():
    path = ROOT / "lab09" / "data" / "orders.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "customer", "item", "item_price_ghs", "delivery_ghs",
                    "order_date", "refunded"])
        for oid, cust, item, price, deliv, ago, refunded in ORDERS:
            w.writerow([oid, cust, item, f"{price:.2f}", f"{deliv:.2f}", d(-ago), refunded])
    print(f"wrote {path.relative_to(ROOT)} ({len(ORDERS)} rows)")


if __name__ == "__main__":
    write_pharmacy()
    write_orders()
