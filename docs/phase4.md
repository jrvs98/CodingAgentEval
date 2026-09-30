# Phase 4 notes — adversarial tasks

Phase 4 adds six tasks designed to expose failure modes that ordinary feature
tasks do not reliably catch. They are separate from the original 18-task
benchmark, so the baseline comparison remains stable.

## Adversarial task set

| Task | Failure mode targeted |
|---|---|
| `adv-nc-01` | Feature interaction: case-insensitive tags plus archive visibility |
| `adv-inv-01` | Silent acceptance of an invalid sort parameter |
| `adv-inv-02` | Missing validation for zero, negative, boolean, and fractional input |
| `adv-sr-01` | Nondeterministic output when top-N revenues tie |
| `adv-sr-02` | Malformed and reversed date ranges accepted by the CLI |
| `adv-sr-03` | Unknown transaction types silently treated as refunds |

Each task has a natural-language contract in `tasks/adversarial_tasks.json` and
a separate hidden test under `tasks/hidden_tests/adversarial/`.

## Run the adversarial graders

```
python3 tasks/verify_adversarial.py --all
python3 tasks/verify_adversarial.py adv-inv-02
```

The current solved repositories intentionally fail these new hidden tests. That
is the starting adversarial baseline: baseline suites remain green while all
six new requirements are red. Run them through the Phase 1 and Phase 3 agents,
then append their JSONL records to the existing logs and compare reports.

The failure log to capture for each run should include the task ID, iteration
count, final grader output, cost, latency, and any qualitative policy violation.
This makes retry loops, weak input validation, and critic approval mistakes
observable rather than anecdotal.