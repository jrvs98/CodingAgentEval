"""Aggregation functions over a list of Transaction objects."""
from collections import defaultdict


def compute_totals_by_category(transactions):
    """Net revenue per category. Sales add to the total, refunds subtract."""
    totals = defaultdict(float)
    for t in transactions:
        totals[t.category] += t.amount if t.type == "sale" else -t.amount
    return dict(totals)


def compute_monthly_revenue(transactions):
    """Net revenue keyed by calendar month, e.g. '2026-01'."""
    totals = defaultdict(float)
    for t in transactions:
        month_key = "-".join(t.date.split("-")[:2])
        totals[month_key] += t.amount if t.type == "sale" else -t.amount
    return dict(totals)


def top_n_products(transactions, n):
    totals = defaultdict(float)
    for t in transactions:
        totals[t.product] += t.amount if t.type == "sale" else -t.amount
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:n]


def pivot_category_month(transactions):
    pivot = defaultdict(lambda: defaultdict(float))
    for t in transactions:
        month_key = "-".join(t.date.split("-")[:2])
        pivot[t.category][month_key] += t.amount if t.type == "sale" else -t.amount
    return {category: dict(months) for category, months in pivot.items()}
