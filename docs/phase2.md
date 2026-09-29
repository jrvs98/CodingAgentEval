# Phase 2 notes — evaluation harness v1

Phase 2 turns the Phase 1 JSONL output into a comparable report. The report
includes pass rate, median cost, median latency, median iterations, total cost,
and cost per successful task. It also runs qualitative policy checks against
the run metadata.

## Qualitative checks

Each run records the files named by the model's patch. The report flags runs
that touch tests, delete tests, or modify `tasks/` files. These checks catch a
model that improves its score by weakening the evaluation instead of fixing the
target repository.

## Usage

After a baseline run:

```
python3 -m eval.report eval/runs.jsonl
python3 -m eval.report eval/runs.jsonl --json
```

The JSON form is intended for later comparison tables and dashboards. A log
can contain multiple runs; aggregation treats every JSONL row as one run.

The harness tests are stdlib-only:

```
python3 -m unittest discover -s eval
```