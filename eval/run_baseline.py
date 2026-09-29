"""Run the Phase 1 single-agent baseline against one or all tasks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import AgentConfig, AnthropicClient, run_task


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="all", help="task id or 'all'")
    parser.add_argument("--model", default="claude-sonnet-4-5")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--log", type=Path, default=ROOT / "eval" / "runs.jsonl")
    args = parser.parse_args()

    with (ROOT / "tasks" / "tasks.json").open() as stream:
        tasks = json.load(stream)
    selected = tasks if args.task == "all" else [task for task in tasks if task["id"] == args.task]
    if not selected:
        parser.error(f"unknown task id: {args.task}")

    client = AnthropicClient(args.model)
    config = AgentConfig(max_iterations=args.max_iterations)
    for task in selected:
        record = run_task(task, ROOT / "repos", client, config, args.log)
        print(
            f"{record['task_id']}: {'PASS' if record['passed'] else 'FAIL'} "
            f"iterations={record['iterations']} latency={record['latency_seconds']}s "
            f"cost=${record['cost_usd']:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())