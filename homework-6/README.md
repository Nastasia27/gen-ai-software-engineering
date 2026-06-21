# AI-Powered Multi-Agent Banking Pipeline

**Created by Anastasia Kopiika.**

A capstone project that processes banking transactions through a chain of
independent agents. Each transaction is validated, scored for fraud risk, and
(if approved) settled — and every stage is observable as JSON files moving
across a shared workspace. The system is wrapped in Claude Code automation:
custom Skills run the pipeline, a coverage-gate hook protects the test suite,
and a FastMCP server makes the results queryable from any MCP client.

The data path is deliberately deterministic and money-safe: amounts use
Python's `Decimal` with `ROUND_HALF_UP` (never `float`), risk timing is read
from each transaction's own timestamp (never the wall clock), and sensitive
fields (account numbers) are masked in the audit log. Running the pipeline over
the 8 sample transactions yields **5 settled, 1 flagged, 2 rejected**.

## Agents

- **Agent 1 — Transaction Validator** (`agents/transaction_validator.py`):
  gatekeeper. Checks required fields, a positive amount, and a valid ISO 4217
  currency. Produces `validated` or `rejected` (with a reason) — never raises.
- **Agent 2 — Fraud Detector** (`agents/fraud_detector.py`): scores each
  validated transaction (high value, very high value, cross-border, off-hours)
  to a 0–100 risk score; `flagged` for manual review at ≥ 70, else `approved`.
- **Agent 3 — Settlement Processor** (`agents/settlement_processor.py`): settles
  approved transactions, computing net = gross − 0.1% fee with `Decimal`
  (0 decimals for JPY). `flagged` and `rejected` are recorded, never settled.
- **Orchestrator** (`integrator.py`): the only component that touches files.
  Seeds `shared/input/` from the sample, runs each transaction through the three
  agents, writes a JSON file at every hop, and emits `shared/results/` plus a
  run summary.

## Architecture

```
                         sample-transactions.json
                                   │
                                   ▼
                          ┌──────────────────┐
                          │   integrator.py  │  (orchestrator — owns all file I/O)
                          └──────────────────┘
                                   │  for each transaction, written at every hop:
                                   ▼
        shared/input ──► shared/processing ──► shared/output ──► shared/results
                                   │
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                         ▼
   ┌───────────────┐      ┌────────────────┐      ┌──────────────────────┐
   │   Agent 1     │ ───► │    Agent 2     │ ───► │      Agent 3         │
   │   Validator   │      │ Fraud Detector │      │ Settlement Processor │
   │ validated /   │      │  approved /    │      │  settled (or         │
   │  rejected     │      │   flagged      │      │  flagged/rejected)   │
   └───────────────┘      └────────────────┘      └──────────────────────┘
                                   │
                                   ▼
                  shared/results/*.json  +  _summary.json
                                   │
                                   ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │  Surrounding automation (Claude Code)                                  │
   │   • Skills:  /run-pipeline · /validate-transactions · /write-spec      │
   │   • Hook:    coverage gate — blocks push if test coverage < 80%        │
   │   • MCP:     context7 (docs) + pipeline-status (query results)         │
   │   • Tests:   pytest + pytest-cov (96% coverage)                        │
   └───────────────────────────────────────────────────────────────────────┘
```

## Tech stack

| Area | Choice |
|---|---|
| Language | Python 3.10+ (core pipeline & tests also run on 3.9) |
| Money / rounding | stdlib `decimal.Decimal` with `ROUND_HALF_UP` |
| Messaging | file-based JSON envelopes across `shared/{input,processing,output,results}/` |
| Tests | `pytest` + `pytest-cov` (coverage gate at 80%, achieved 96%) |
| MCP server | `FastMCP` (STDIO transport) |
| External MCP | `context7` (library documentation lookup) |
| Automation | Claude Code Skills (`.claude/commands/`) + coverage-gate hook |
| Runtime helper | `uv` (provides Python 3.12 + FastMCP for the MCP server) |

## Repository layout

```
homework-6/
├── agents/                 # the three pipeline agents + shared helpers (common.py)
├── integrator.py           # orchestrator
├── mcp/server.py           # custom FastMCP server (pipeline-status)
├── mcp.json                # MCP config: context7 + pipeline-status
├── scripts/                # coverage_gate.py + git/Claude push hooks
├── tests/                  # unit tests per agent + integration test
├── shared/                 # runtime workspace (input/processing/output/results)
├── .claude/                # Skills (commands/) + settings.json (hook)
├── sample-transactions.json
├── specification.md · agents.md · research-notes.md
└── docs/screenshots/       # the 5 required screenshots
```

See **[HOWTORUN.md](HOWTORUN.md)** for step-by-step setup and a demo.
