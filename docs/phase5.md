# Phase 5 notes — guardrails and failure instrumentation

Phase 5 makes the agent loop bounded and auditable after the adversarial
baseline exposed the risks of unvalidated inputs and runaway retries.

## Guardrails shipped

- `--max-iterations` remains a hard retry cap.
- `--max-cost-usd` stops a task before applying an over-budget model response.
- Patches touching `tests/`, deleting files, or touching `tasks/` are rejected
  before execution by both runners.
- Every run records a machine-readable `failure_reason`: `budget_exceeded`,
  `policy_violation`, `patch_rejected`, `grader_failed`, `critic_rejected`,
  `agent_error`, or `iteration_limit`.
- Reports aggregate failure reasons so retry loops and budget failures can be
  compared instead of buried in free-form logs.

## Usage

```
python3 -m eval.run_baseline --task nc-01 --max-iterations 3 --max-cost-usd 1.00
python3 -m eval.run_multi_agent --task adv-inv-02 --max-iterations 3 --max-cost-usd 1.00
python3 -m eval.report eval/multi_agent_runs.jsonl --json
```

Run the adversarial set through both configurations for a comparable report:

```
./.venv/bin/python -m eval.run_baseline --provider gemini --model gemini-3.8-flash \
  --tasks-file tasks/adversarial_tasks.json --task all \
  --max-iterations 3 --max-cost-usd 1.00 --log /tmp/phase5-baseline.jsonl
./.venv/bin/python -m eval.run_multi_agent --provider gemini --model gemini-3.8-flash \
  --tasks-file tasks/adversarial_tasks.json --task all \
  --max-iterations 3 --max-cost-usd 1.00 --log /tmp/phase5-multi.jsonl
cat /tmp/phase5-baseline.jsonl /tmp/phase5-multi.jsonl > /tmp/phase5-combined.jsonl
./.venv/bin/python -m eval.report /tmp/phase5-combined.jsonl --json
```

Use `--task adv-inv-02` instead of `--task all` for a one-task smoke test.

The cost ceiling is an estimate based on provider-reported token usage and the
configured per-million-token rates. It is intentionally enforced before patch
application; a provider response that would exceed the ceiling cannot mutate
the temporary repository or trigger another retry.

The six adversarial tasks remain a red baseline until the agents are run
against them. Phase 5's implementation is the guardrail layer and telemetry;
the before/after live numbers should be generated with the same task logs and
reported in the next iteration.