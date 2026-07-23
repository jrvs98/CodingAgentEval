"""CSV loading for sales transactions."""
import csv
from dataclasses import dataclass


@dataclass
class Transaction:
    date: str       # ISO date, "YYYY-MM-DD"
    category: str
    product: str
    amount: float   # always stored positive; `type` says whether it's a sale or a refund
    type: str       # "sale" or "refund"


def load_transactions(csv_path):
    """Read a transactions CSV (columns: date,category,product,amount,type)."""
    transactions = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(
                Transaction(
                    date=row["date"],
                    category=row["category"],
                    product=row["product"],
                    amount=float(row["amount"]),
                    type=row["type"],
                )
            )
    return transactions
