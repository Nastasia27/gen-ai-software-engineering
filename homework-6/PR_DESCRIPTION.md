# Homework 6 — MCP Integration (Task 4)

**Author: Anastasia Kopiika**

Adds MCP integration to the banking pipeline: a custom FastMCP server that makes
the pipeline results queryable, plus `context7` for documentation lookups during
development. Both servers are configured in a single `mcp.json`.

## Changes

- **`mcp/server.py`** — custom FastMCP server `pipeline-status` (STDIO transport):
  - tool `get_transaction_status(transaction_id)` — one transaction's stored
    outcome from `shared/results/` (graceful "not found" if absent)
  - tool `list_pipeline_results()` — summary of every processed transaction + tally
  - resource `pipeline://summary` — the latest run summary (`_summary.json`) as text
- **`mcp.json`** — both servers: `context7` (via `npx`) and `pipeline-status`.
  The custom server is launched through `uv` (Python 3.12 + FastMCP), since the
  system `python3` is 3.9 and FastMCP needs ≥ 3.10.
- **`research-notes.md`** — 2 context7 queries documented (Decimal/`ROUND_HALF_UP`
  and the FastMCP tool/resource decorators).

## Verification

The server was launched over real STDIO using the exact command from `mcp.json`;
all tools and the resource respond, e.g. `get_transaction_status("TXN005")` →
`flagged / high / 70`.

## MCP interaction

One Claude Code session exercising both servers: a `context7` docs lookup for the
FastMCP resource decorator, then a call to the custom `pipeline-status` tool
`get_transaction_status("TXN005")`.

![MCP interaction](homework-6/docs/screenshots/mcp-interaction.png)
