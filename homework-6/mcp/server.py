"""Custom FastMCP server: makes the banking pipeline queryable (Task 4).

Exposes the pipeline's ``shared/results/`` tree over MCP so a client (Claude
Code, etc.) can ask about processed transactions without reading files itself:

  - tool  ``get_transaction_status(transaction_id)`` — one transaction's outcome
  - tool  ``list_pipeline_results()``                — summary of every result
  - resource ``pipeline://summary``                  — latest run summary as text

Transport is STDIO (``mcp.run()`` with no args): the client spawns this server
per session, so nothing here relies on staying resident (see research-notes.md
§Query 2). Run it standalone with: ``python mcp/server.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP

# shared/results lives one level up from this file (repo root / shared / results).
REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "shared" / "results"
SUMMARY_FILE = RESULTS_DIR / "_summary.json"

mcp = FastMCP("pipeline-status")


# --- helpers (pure file reads, kept out of the tool bodies) ------------------


def _read_json(path: Path) -> dict | None:
    """Return parsed JSON for ``path``, or None if it is missing/unreadable."""
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _result_files() -> list[Path]:
    """All per-transaction result files (excludes the _summary.json aggregate)."""
    if not RESULTS_DIR.is_dir():
        return []
    return sorted(p for p in RESULTS_DIR.glob("*.json") if p.name != "_summary.json")


def _outcome(envelope: dict) -> dict:
    """Flatten a stored envelope into the fields a caller actually cares about."""
    data = envelope.get("data", {})
    return {
        "transaction_id": data.get("transaction_id"),
        "status": data.get("status"),
        "risk_level": data.get("risk_level"),
        "risk_score": data.get("risk_score"),
        "reason": data.get("reason"),          # set only for rejected transactions
        "settlement": data.get("settlement"),  # set only for settled transactions
    }


# --- tools -------------------------------------------------------------------


@mcp.tool
def get_transaction_status(transaction_id: str) -> dict:
    """Return the stored outcome for one transaction from ``shared/results/``.

    Args:
        transaction_id: e.g. "TXN001".

    Returns the transaction's final status (settled / flagged / rejected) plus
    risk and settlement details. ``found`` is False if the pipeline never
    produced a result for that id.
    """
    envelope = _read_json(RESULTS_DIR / f"{transaction_id}.json")
    if envelope is None:
        return {
            "transaction_id": transaction_id,
            "found": False,
            "message": f"No result for {transaction_id}. Run the pipeline first (python integrator.py).",
        }
    return {"found": True, **_outcome(envelope)}


@mcp.tool
def list_pipeline_results() -> dict:
    """Return a summary of every processed transaction.

    Combines the aggregate tally from ``_summary.json`` with a per-transaction
    list rebuilt from the individual result files.
    """
    results = [_outcome(env) for p in _result_files() if (env := _read_json(p))]
    summary = _read_json(SUMMARY_FILE) or {}
    return {
        "count": len(results),
        "tally": summary.get("tally"),
        "rejections": summary.get("rejections"),
        "results": results,
    }


# --- resource ----------------------------------------------------------------


@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    """The latest pipeline run summary (``_summary.json``) as pretty text."""
    summary = _read_json(SUMMARY_FILE)
    if summary is None:
        return "No pipeline summary yet. Run the pipeline first: python integrator.py"
    return json.dumps(summary, indent=2)


if __name__ == "__main__":
    mcp.run()  # STDIO transport — matches the mcp.json command/args launch model
