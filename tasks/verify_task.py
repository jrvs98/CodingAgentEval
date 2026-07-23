#!/usr/bin/env python3
"""Run a single task's grading check against its repo.

For a given task id, this:
  1. Runs the repo's own baseline test suite (must stay green -- this is the
     "don't break existing behavior" contract).
  2. Runs the task's hidden test file (this is what actually grades the task).

This is the seed of the Phase 1/2 eval harness: any future agent (baseline or
multi-agent) gets scored by pointing this same script at the repo it edited.

Usage:
    python3 verify_task.py <task_id>       # run one task
    python3 verify_task.py --all           # run every task in tasks.json
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS_PATH = os.path.join(ROOT, "tasks.json")
REPOS_ROOT = os.path.join(ROOT, "..", "repos")


def load_tasks():
    with open(TASKS_PATH) as f:
        return {t["id"]: t for t in json.load(f)}


def run(cmd, cwd, env, timeout=60):
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def verify_one(task, quiet=False):
    repo_dir = os.path.abspath(os.path.join(REPOS_ROOT, task["repo"]))
    hidden_test = os.path.abspath(os.path.join(ROOT, "..", task["hidden_test"]))

    env = dict(os.environ)
    env["PYTHONPATH"] = repo_dir

    code, out, err = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], repo_dir, env)
    baseline_ok = code == 0

    code, out, err = run([sys.executable, hidden_test], repo_dir, env)
    hidden_ok = code == 0
    hidden_err = err

    if not quiet:
        print(f"== {task['id']}: {task['title']} ==")
        print(f"  baseline suite: {'PASS' if baseline_ok else 'FAIL'}")
        print(f"  hidden test:    {'PASS' if hidden_ok else 'FAIL'}")
        if not hidden_ok:
            print("  --- hidden test output (tail) ---")
            print("  " + "\n  ".join(hidden_err.strip().splitlines()[-8:]))

    return baseline_ok, hidden_ok


def main():
    tasks = load_tasks()

    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        rows = []
        for task_id, task in tasks.items():
            baseline_ok, hidden_ok = verify_one(task)
            rows.append((task_id, baseline_ok, hidden_ok))
        print("\n=== summary ===")
        for task_id, baseline_ok, hidden_ok in rows:
            status = "PASS" if (baseline_ok and hidden_ok) else "FAIL"
            print(f"{task_id:8s} baseline={'ok' if baseline_ok else 'FAIL':5s} hidden={'ok' if hidden_ok else 'FAIL':5s} -> {status}")
        sys.exit(0)

    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    task_id = sys.argv[1]
    if task_id not in tasks:
        print(f"unknown task id: {task_id}")
        sys.exit(2)

    baseline_ok, hidden_ok = verify_one(tasks[task_id])
    overall = baseline_ok and hidden_ok
    print(f"TASK RESULT: {'PASS' if overall else 'FAIL'}")
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
