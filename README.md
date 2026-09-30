# Coding Agent Eval

A multi-agent system that takes a coding task — bug fix, feature add,
refactor — against a small existing codebase, plans it, writes the code,
tests it, and iterates until it passes. Built alongside an evaluation harness
that scores every run on pass rate, cost, latency, and iteration count.

Most "AI coding agent" repos are demos. The eval harness is the point here:
every agent version gets scored against the same task set, so claims like
"multi-agent beats single-agent" have to survive a side-by-side number, not
just a vibe.

## Status

Phase 0 is done: 3 toy codebases with seeded bugs, an 18-task scored set, and
a working grading script. Phase 1 now has a single-agent baseline runner; live
scores are not claimed until it has been run with an API key. This section gets
updated as each phase ships; no results are claimed here until they exist.

- [x] **Phase 0** — Toy repos, 18-task set, hidden grading tests ([notes](docs/phase0.md))
- [x] **Phase 1** — Single-agent baseline runner ([notes](docs/phase1.md))
- [x] **Phase 2** — Eval harness v1 (pass rate / cost / latency report) ([notes](docs/phase2.md))
- [x] **Phase 3** — Multi-agent architecture (Planner / Coder / Critic) ([notes](docs/phase3.md))
- [x] **Phase 4** — Adversarial tasks — break it on purpose, document failures ([notes](docs/phase4.md))
- [x] **Phase 5** — Guardrails and failure instrumentation ([notes](docs/phase5.md))
- [ ] **Phase 6** — Packaging (this README, architecture diagram, write-up)
- [ ] **Phase 7** — Stretch goals (cost routing, security reviewer, dashboard)

## Why this scope

- **Not HumanEval-style single-function tasks.** Those are saturated and a
  single LLM call one-shots most of them — they don't justify a multi-agent
  design.
- **Not a framework demo.** The agent loop is hand-built for v1, not a
  `.compile()` call on LangGraph/CrewAI. Understanding why an orchestrator
  retries a failed step instead of giving up is the actual skill being shown.
- **Not a fine-tune or from-scratch model.** This project is about
  orchestration, evaluation, and production judgment — not model training.

## Repo layout

```
repos/                  toy codebases the agent operates on
  notes-cli/              CLI note-taking tool
  inventory-api/          inventory REST-style service
  sales-report/           CSV sales data pipeline
tasks/
  tasks.json               18 scored tasks: id, repo, description, pass condition
  adversarial_tasks.json   6 Phase 4 stress tasks
  hidden_tests/<repo>/      one grading test per task -- not shown to the agent
  verify_task.py            run a task's grading check against its repo
  verify_adversarial.py    run the Phase 4 adversarial grading set
docs/
  phase0.md                 Phase 0 build notes, seeded-bug list, deviations
eval/                    eval harness and Phase 1 output
  agent.py                isolated single-agent loop and Anthropic adapter
  run_baseline.py         CLI for one task or the full task set
  report.py               JSONL aggregation and qualitative policy report
  multi_agent.py          Planner/Coder/Critic roles and orchestrator
  run_multi_agent.py      CLI for the multi-agent runner
  test_agent.py           fake-client regression test (no API call)
  test_report.py          report and policy-check regression tests
  test_multi_agent.py     multi-agent orchestration regression test
```

## The task set

18 tasks across 3 small (150-300 line) codebases: 9 bug fixes, 6 feature
additions, 3 tasks that span multiple files. Every task has a natural-language
description and an objective pass/fail condition — the repo's existing test
suite must still pass, and a task-specific hidden test must pass. No vague
"make this better" tasks; if it can't be scored, it's not in the set.

| Repo | What it does | Bug flavor | Missing features |
|---|---|---|---|
| `notes-cli` | CLI note tool, JSON storage | case-sensitive search, ID reuse after delete, swapped sort logic | tag filter, archive/unarchive, CSV export |
| `inventory-api` | stdlib WSGI + SQLite item service | case-sensitive filter, exclusive price boundary, partial updates null out fields | sort param, restock endpoint, low-stock endpoint |
| `sales-report` | CSV revenue aggregation | refunds added instead of subtracted, months merged across years, float rounding errors | top-N products, date-range filter, category/month pivot |

Every task was verified solvable before being added: baseline suite green,
hidden test red on the seeded repo, a hand-written fix turns it green, then
reverted back to seeded state. Full methodology in
[`docs/phase0.md`](docs/phase0.md).

## Running it

Everything is Python stdlib — no pip install required.

```bash
# run a toy repo's own test suite
cd repos/notes-cli && python3 -m unittest discover -s tests

# check one task's grading result
cd tasks && python3 verify_task.py nc-01

# check all 18
cd tasks && python3 verify_task.py --all

# run the Phase 1 baseline for one task (requires ANTHROPIC_API_KEY)
python3 -m eval.run_baseline --task nc-01

# use Gemini instead (requires GEMINI_API_KEY and google-genai)
python3 -m eval.run_baseline --provider gemini --model gemini-3.8-flash --task nc-01

# run all tasks and append JSONL metrics to eval/runs.jsonl
python3 -m eval.run_baseline --task all

# summarize a run log as text
python3 -m eval.report eval/runs.jsonl

# emit the same report as machine-readable JSON
python3 -m eval.report eval/runs.jsonl --json

# run the Phase 3 multi-agent version
python3 -m eval.run_multi_agent --task nc-01

# run Phase 3 with Gemini
python3 -m eval.run_multi_agent --provider gemini --model gemini-3.8-flash --task nc-01

# run the Phase 4 adversarial graders
python3 tasks/verify_adversarial.py --all

# cap a live task at three iterations and one dollar of estimated model cost
python3 -m eval.run_multi_agent --provider gemini --task adv-inv-02 \
  --max-iterations 3 --max-cost-usd 1.00
```

## Design decisions

**No third-party frameworks in the toy repos.** `inventory-api` is a
hand-rolled stdlib WSGI app instead of FastAPI/Flask, and tests use
`unittest` instead of `pytest`. This means the agent loop never needs a
pip-install step before running tests — one less source of cost, latency, and
flakiness once Phase 1-3 start burning API budget. `pytest` is still
compatible with these test files if preferred later.

**Hidden tests are separate from the visible repo.** The agent only ever sees
`tasks.json`'s natural-language description, never the grading test. That's
what keeps pass/fail an objective signal instead of the agent grading its own
homework.

## Tech stack

Python · Claude API (Anthropic SDK) · subprocess/Docker sandboxing for
agent-generated code · SQLite/JSONL for eval logs.

## License

TBD.
