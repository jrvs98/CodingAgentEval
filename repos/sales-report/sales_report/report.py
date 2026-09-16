"""Human-readable report generation."""
from decimal import Decimal, ROUND_HALF_UP

from .aggregate import compute_totals_by_category, compute_monthly_revenue


def format_currency(amount):
    """Format a float amount as a dollar string, e.g. 19.999 -> '$20.00'."""
    rounded = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"${rounded:.2f}"


def generate_report(transactions):
    by_category = compute_totals_by_category(transactions)
    by_month = compute_monthly_revenue(transactions)
    from .aggregate import pivot_category_month
    by_category_month = pivot_category_month(transactions)

    lines = ["=== Revenue by Category ==="]
    for cat, total in sorted(by_category.items()):
        lines.append(f"{cat}: {format_currency(total)}")

    lines.append("")
    lines.append("=== Revenue by Month ===")
    for month, total in sorted(by_month.items()):
        lines.append(f"{month}: {format_currency(total)}")

    lines.append("")
    lines.append("=== Category by Month ===")
    for category, months in sorted(by_category_month.items()):
        for month, total in sorted(months.items()):
            lines.append(f"{category} {month}: {format_currency(total)}")

    return "\n".join(lines)
