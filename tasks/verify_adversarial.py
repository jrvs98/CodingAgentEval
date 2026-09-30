#!/usr/bin/env python3
"""Run the Phase 4 adversarial grading set."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPOS_ROOT = os.path.join(ROOT, "..", "repos")
TASKS_PATH = os.path.join(ROOT, "adversarial_tasks.json")


def run(command, cwd, env, timeout=60):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr


def verify_one(task):
    repo_dir = os.path.abspath(os.path.join(REPOS_ROOT, task["repo"]))
    hidden_test = os.path.abspath(os.path.join(ROOT, "..", task["hidden_test"]))
    env = {**os.environ, "PYTHONPATH": repo_dir}
    baseline_code, baseline_out, baseline_err = run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"], repo_dir, env
    )
    hidden_code, hidden_out, hidden_err = run([sys.executable, hidden_test], repo_dir, env)
    baseline_ok = baseline_code == 0
    hidden_ok = hidden_code == 0
    print(f"{task['id']}: baseline={'PASS' if baseline_ok else 'FAIL'} hidden={'PASS' if hidden_ok else 'FAIL'}")
    if not baseline_ok or not hidden_ok:
        output = (baseline_out + baseline_err + hidden_out + hidden_err).strip().splitlines()
        print("  " + "\n  ".join(output[-6:]))
    return baseline_ok and hidden_ok


def main():
    with open(TASKS_PATH) as stream:
        tasks = json.load(stream)
    selected = tasks
    if len(sys.argv) == 2 and sys.argv[1] != "--all":
        selected = [task for task in tasks if task["id"] == sys.argv[1]]
        if not selected:
            print(f"unknown adversarial task id: {sys.argv[1]}")
            return 2
    elif len(sys.argv) not in (1, 2):
        print("usage: verify_adversarial.py [task_id|--all]")
        return 2
    passed = sum(verify_one(task) for task in selected)
    print(f"\nAdversarial summary: {passed}/{len(selected)} passed")
    return 0 if passed == len(selected) else 1


if __name__ == "__main__":
    raise SystemExit(main())