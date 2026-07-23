"""Aggregation functions over a list of Transaction objects."""
from collections import defaultdict


def compute_totals_by_category(transactions):
    """Net revenue per category. Sales add to the total, refunds subtract."""
    totals = defaultdict(float)
    for t in transactions:
        totals[t.category] += t.amount
    return dict(totals)


def compute_monthly_revenue(transactions):
    """Net revenue keyed by calendar month, e.g. '2026-01'."""
    totals = defaultdict(float)
    for t in transactions:
        month_key = t.date.split("-")[1]
        totals[month_key] += t.amount
    return dict(totals)
