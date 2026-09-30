# Phase 1 notes — single-agent baseline

Phase 1 adds a deliberately simple control group before any specialized
multi-agent roles exist. The runner gives one model the task description and
visible repository files, asks for a unified diff, applies it in a temporary
copy, and runs the existing baseline suite plus that task's hidden grader.

## Run it

Install the Anthropic SDK and set `ANTHROPIC_API_KEY` in the shell:

```
python3 -m pip install anthropic
export ANTHROPIC_API_KEY=...
python3 -m eval.run_baseline --task nc-01
```

Gemini is supported through Google's Gen AI SDK:

```
python3 -m pip install google-genai
export GEMINI_API_KEY=...
python3 -m eval.run_baseline --provider gemini --model gemini-3.5-flash-lite --task nc-01
```

Credentials are read from the environment and are never written to run logs.

Use `--task all` for the full 18-task control group. `--max-iterations` caps
retries, and `--log` changes the JSONL output path.

Each JSONL row records the task, pass/fail result, iterations, latency, token
usage, estimated cost, timestamp, and the final failure excerpt when relevant.
The agent never receives `tasks/hidden_tests`, and the original toy repository
is never modified: every task runs in a temporary copy.

The fake-client test validates the loop without an API call:

```
python3 -m unittest eval.test_agent
```

No live Phase 1 scores are included yet because they require an API key and a
deliberate model/configuration choice. Those results become the control group
for Phase 3 comparisons.