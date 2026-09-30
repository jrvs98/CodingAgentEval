# GitHub provider

The runners now default to the `github` provider. It uses the supported GitHub
Models inference API, which is the stable API route for GitHub-hosted models.
It is not an unofficial direct Copilot subscription endpoint.

Authenticate with either an environment token:

```
export GITHUB_TOKEN="..."
```

or the GitHub CLI:

```
gh auth login
```

Then run a task:

```
./.venv/bin/python -m eval.run_multi_agent \
  --provider github \
  --model openai/gpt-4.1 \
  --tasks-file tasks/adversarial_tasks.json \
  --task adv-inv-02 \
  --max-iterations 1 \
  --max-cost-usd 1.00
```

The adapter reads token usage from the API response and never writes the token
to run logs. Model availability and quotas depend on the GitHub account and
organization policy.