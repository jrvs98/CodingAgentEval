"""Command-line entry point for sales-report."""
import argparse

from .loader import load_transactions
from .report import generate_report


def build_parser():
    parser = argparse.ArgumentParser(prog="sales-report")
    parser.add_argument("csv_path")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    transactions = load_transactions(args.csv_path)
    print(generate_report(transactions))


if __name__ == "__main__":
    main()
