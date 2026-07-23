# Phase 0 notes — task design

Phase 0 deliverable: 3 toy repos with real bugs and missing features, an
18-task scored task set, and a working verification script. No agent code
yet — that's Phase 1.

## The 3 repos, and what's wrong with each

**notes-cli** — add/list/delete/search notes in a JSON file.
Seeded bugs: search is case-sensitive when it shouldn't be; note IDs get reused
after a delete; `list --sort` has its date/title branches swapped.
Missing features: tag filtering, archive/unarchive, CSV export.

**inventory-api** — CRUD + filtering over a SQLite-backed item table, exposed
as a WSGI app (no Flask/FastAPI — see "Deviations" below).
Seeded bugs: category filter is case-sensitive; `max_price` excludes the exact
boundary value; partial updates null out fields the caller didn't send.
Missing features: `sort_by` query param, a restock endpoint, a low-stock endpoint.

**sales-report** — loads a transactions CSV, aggregates revenue by category
and month, prints a text report.
Seeded bugs: refunds get added instead of subtracted; monthly totals merge the
same month across different years; currency rounding breaks on float precision
edge cases (e.g. 2.675 rounds down instead of up).
Missing features: top-N products, CLI date-range filter, category-by-month pivot.

Each repo has 6 tasks: 3 bug fixes, 2 feature adds, 1 task that spans multiple
files. 3 repos x 6 tasks = 18, all listed in `tasks/tasks.json`.

## How grading works

For each task, `tasks/verify_task.py <task_id>` runs two things against the
repo: the repo's own baseline suite (must stay green — this is the "don't
break what already works" contract) and the task's hidden test (this is what
actually scores the task). Both must pass for a PASS.

```
python3 tasks/verify_task.py nc-01        # one task
python3 tasks/verify_task.py --all        # all 18
```

Right now `--all` shows baseline=ok, hidden=FAIL across the board — that's
expected. The repos are still in their seeded (buggy/incomplete) state; nothing
has fixed them yet. That's the job for Phase 1's agent.

## How every task was verified solvable

Vague or broken tasks can't be scored, so I didn't just write the hidden tests
and hope. For all 18 tasks I: confirmed the baseline suite passes on the
seeded repo, confirmed the hidden test fails on the seeded repo (proving the
task isn't already done), hand-wrote a correct fix, confirmed the hidden test
then passes with the baseline suite still green, then reverted the repo back
to its seeded state. All 18 round-tripped cleanly.

One bug surfaced during this process: the first cut of the sales-report
baseline suite hard-coded the buggy month-key format ("01" instead of
"2026-01"), so a correct fix for sr-02 would have broken baseline tests that
shouldn't have cared about that detail. Fixed by loosening that assertion to
check behavior, not the exact key format under test. Worth remembering for
later phases: baseline tests that accidentally encode a bug's behavior will
make correct fixes look like regressions — a false-positive failure mode
that's easy to miss just by staring at pass/fail counts.

## Deviations from the original plan, and why

**No FastAPI/Flask, no pytest.** The build environment used for Phase 0 had
no outbound pip access. Rather than block on that, inventory-api is a
hand-rolled stdlib WSGI app (routes, JSON in/out, SQLite) tested with a
~20-line WSGI test client, and all three repos use `unittest` instead of
`pytest`. This isn't just a workaround — it means the agent loop in Phase 1-3
never needs a pip-install step before running tests, which removes a real
source of cost, latency, and flakiness later. `pytest` can still collect and
run these same test files if you want it (it understands `unittest.TestCase`),
and swapping inventory-api for a real FastAPI app later is a contained change
— the routing and SQLite logic in `app/db.py` don't need to move.

**No git history from the build session.** The environment used to build
Phase 0 had a filesystem quirk where git's lockfiles couldn't be deleted once
created, so the repo's actual git history starts fresh from whoever runs
`git init` locally, not from the build session.
