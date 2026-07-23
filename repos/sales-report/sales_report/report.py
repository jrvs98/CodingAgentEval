"""Human-readable report generation."""
from .aggregate import compute_totals_by_category, compute_monthly_revenue


def format_currency(amount):
    """Format a float amount as a dollar string, e.g. 19.999 -> '$20.00'."""
    return f"${round(amount, 2):.2f}"


def generate_report(transactions):
    by_category = compute_totals_by_category(transactions)
    by_month = compute_monthly_revenue(transactions)

    lines = ["=== Revenue by Category ==="]
    for cat, total in sorted(by_category.items()):
        lines.append(f"{cat}: {format_currency(total)}")

    lines.append("")
    lines.append("=== Revenue by Month ===")
    for month, total in sorted(by_month.items()):
        lines.append(f"{month}: {format_currency(total)}")

    return "\n".join(lines)
