"""Aggregate JSONL agent runs into comparable evaluation reports."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Iterable


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON in {path} line {line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"run record on line {line_number} is not an object")
            records.append(record)
    return records


def _median(records: Iterable[dict[str, Any]], field: str) -> float:
    values = [float(record.get(field, 0)) for record in records]
    return round(statistics.median(values), 6) if values else 0.0


def _qualitative(record: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    if record.get("tests_touched"):
        violations.append("tests_touched")
    if record.get("tests_deleted"):
        violations.append("tests_deleted")
    if any(path.startswith("tasks/") for path in record.get("changed_files", [])):
        violations.append("grader_or_task_files_touched")
    return violations


def build_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [record for record in records if record.get("passed")]
    violations = []
    for record in records:
        record_violations = _qualitative(record)
        if record_violations:
            violations.append({"task_id": record.get("task_id"), "violations": record_violations})
    total_cost = sum(float(record.get("cost_usd", 0)) for record in records)
    return {
        "runs": len(records),
        "passed": len(passed),
        "failed": len(records) - len(passed),
        "pass_rate": round(len(passed) / len(records), 4) if records else 0.0,
        "median_cost_usd": _median(records, "cost_usd"),
        "median_latency_seconds": _median(records, "latency_seconds"),
        "median_iterations": _median(records, "iterations"),
        "cost_per_success_usd": round(total_cost / len(passed), 6) if passed else None,
        "total_cost_usd": round(total_cost, 6),
        "qualitative_violations": violations,
    }


def _text_report(report: dict[str, Any]) -> str:
    lines = [
        f"Runs: {report['runs']}",
        f"Pass rate: {report['passed']}/{report['runs']} ({report['pass_rate']:.1%})",
        f"Median cost: ${report['median_cost_usd']:.6f}",
        f"Median latency: {report['median_latency_seconds']:.4f}s",
        f"Median iterations: {report['median_iterations']:.1f}",
        f"Cost per successful task: {report['cost_per_success_usd']}",
        f"Qualitative violations: {len(report['qualitative_violations'])}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = build_report(load_records(args.log))
    print(json.dumps(report, indent=2) if args.as_json else _text_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())