"""Command-line entry point for sales-report."""
import argparse

from .loader import load_transactions
from .report import generate_report


def build_parser():
    parser = argparse.ArgumentParser(prog="sales-report")
    parser.add_argument("csv_path")
    parser.add_argument("--start")
    parser.add_argument("--end")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    transactions = load_transactions(args.csv_path)
    if args.start:
        transactions = [t for t in transactions if t.date >= args.start]
    if args.end:
        transactions = [t for t in transactions if t.date <= args.end]
    print(generate_report(transactions))


if __name__ == "__main__":
    main()
