# How to run

Step-by-step from a fresh checkout to a full demo. Run every command from the
`homework-6/` directory.

```bash
cd homework-6
```

## 0. Prerequisites

- **Python 3.9+** — runs the pipeline and the test suite.
- **[uv](https://docs.astral.sh/uv/)** — runs the MCP server (FastMCP needs
  Python ≥ 3.10; `uv` provides it automatically, so you don't have to install
  3.10+ yourself).
- **Node.js / npx** — only for the `context7` MCP server.

## 1. Install dependencies (pipeline + tests)

```bash
pip3 install pytest pytest-cov
```

> FastMCP (for the MCP server in step 5) is **not** installed here — `uv`
> pulls it in on demand. Installing it under Python 3.9 would fail.

## 2. Run the pipeline

```bash
python3 integrator.py
```

Expected: the orchestrator seeds `shared/input/`, runs all 8 sample
transactions through the three agents, and prints a summary —
**5 settled, 1 flagged, 2 rejected**. Per-transaction JSON lands in
`shared/results/`, plus an aggregate `shared/results/_summary.json`.
📸 `docs/screenshots/pipeline-run.png`

To see just the validation stage:

```bash
python3 agents/transaction_validator.py --dry-run
```

## 3. Run the tests with coverage

```bash
python3 scripts/coverage_gate.py
```

This is the single source of truth for the gate — it runs
`pytest --cov=agents --cov=integrator --cov-fail-under=80`. Expected:
**61 passed, total coverage ~96%**, and `✅ Coverage gate PASSED`.
📸 `docs/screenshots/test-coverage.png`

## 4. Skills & the coverage-gate hook (Claude Code)

The custom Skills live in `.claude/commands/`. Launch Claude Code **from this
directory** so it picks them up:

```bash
claude          # run inside homework-6/
```

- `/run-pipeline` — runs the pipeline via the agent. 📸 `skill-run-pipeline.png`
- `/validate-transactions` — runs validation only.
- `/write-spec` — regenerates the specification from the template.

**Coverage-gate hook.** `.claude/settings.json` registers a hook that blocks
`git push` when coverage is below 80%. The same gate works outside Claude as a
git hook — install it once from the repo root:

```bash
# from the git repo root (gen-ai-software-engineering/)
printf '#!/usr/bin/env bash\npython3 homework-6/scripts/coverage_gate.py\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

Now a `git push` with coverage < 80% is aborted (exit 1).
📸 `docs/screenshots/hook-trigger.png`

## 5. MCP server (query the pipeline results)

The MCP config in `mcp.json` declares two servers: `context7` (docs) and our
own `pipeline-status`. To use them in Claude Code, copy the config to the file
Claude reads, then launch Claude from this directory:

```bash
cp mcp.json .mcp.json     # Claude Code reads .mcp.json (mcp.json stays as the deliverable)
claude                    # approve both servers when prompted
```

Then, in the session, exercise both servers in one go, e.g.:

> Use context7 to look up the FastMCP resource decorator, then call the
> pipeline-status tool `get_transaction_status` for `TXN005`.

📸 `docs/screenshots/mcp-interaction.png`

The custom server exposes:

| Kind | Name | Returns |
|---|---|---|
| tool | `get_transaction_status(transaction_id)` | one transaction's stored outcome |
| tool | `list_pipeline_results()` | summary of every processed transaction |
| resource | `pipeline://summary` | the latest run summary as text |

To run the server standalone (STDIO):

```bash
uv run --python 3.12 --with fastmcp python mcp/server.py
```

> Run `python3 integrator.py` (step 2) at least once before querying, so
> `shared/results/` exists for the server to read.
