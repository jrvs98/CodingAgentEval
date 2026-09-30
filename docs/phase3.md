# Phase 3 notes — multi-agent architecture

Phase 3 adds a hand-built multi-agent control variant while keeping the Phase 1
single-agent runner unchanged for comparison.

## Roles

- **Planner** reads the task and visible repository, then identifies files,
  implementation steps, and verification points.
- **Coder** receives the plan and current repository state and returns only a
  unified diff.
- **Critic** combines objective baseline/hidden-test results with a review of
  the patch. It cannot approve a failed grade or a patch that touches tests,
  deletes files, or modifies `tasks/` evaluation files.
- **Orchestrator** owns temporary-repository isolation, bounded retries,
  feedback from the Critic to the next Coder attempt, and run metrics.

## Run it

```
python3 -m eval.run_multi_agent --task nc-01
python3 -m eval.run_multi_agent --task all
```

The CLI defaults to Anthropic, but supports Gemini for all three roles:

```
python3 -m pip install google-genai
export GEMINI_API_KEY="your-key"
python3 -m eval.run_multi_agent --provider gemini --model gemini-3.8-flash --task all
```

The role interfaces accept separate clients, so model routing can be measured
later. Multi-agent rows use `agent: "multi-agent"`, which lets the Phase 2
report split a combined JSONL file into `by_agent` comparisons.

The fake-role test is API-free:

```
python3 -m unittest eval.test_multi_agent
```

No comparative live scores are claimed yet. The next step is to run the same
18 tasks through both runners and compare their reports.