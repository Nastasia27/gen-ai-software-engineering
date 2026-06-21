# agents.md — AI Agent Guidelines for the Multi-Agent Banking Pipeline

> How an AI coding agent should behave while implementing `specification.md` in this folder.
> When this file and a generic best practice disagree, **this file wins** for this codebase.

---

## 1. Source of truth

- The spec is `specification.md` in this directory.
- If the spec is unclear, **ask before coding**. Guessing in a banking context is how audit findings happen.
- A change that invalidates a §2 mid-level objective must update the spec in the same change.

---

## 2. Tech stack (fixed for this project)

- **Python 3.10+**, standard library first: `decimal`, `json`, `uuid`, `logging`, `pathlib`, `datetime`.
- **FastMCP** for the custom MCP server (`mcp/server.py`).
- **pytest + pytest-cov** for tests and the coverage gate.
- No web framework, no database — communication is **JSON files** across `shared/`.
- Do not add a dependency without a one-line justification; stdlib covers almost everything here.

---

## 3. Banking domain rules (non-negotiable)

1. **Money is `Decimal`.** Never `float`/`double`. Parse from string: `Decimal(str(amount))`. Always paired with an ISO 4217 currency.
2. **Settlement rounding is `ROUND_HALF_UP`**, 2dp for most currencies, **0dp for JPY** (zero-decimal currency).
3. **PII is masked in logs.** `source_account`, `destination_account`, and `description` are sensitive — never log them in plaintext. Mask to e.g. `ACC-****`.
4. **Time is UTC.** Timing decisions read the transaction's own `timestamp` field — never `datetime.now()` inside decision logic (keeps tests repeatable).
5. **Every state change is audited.** One structured log line per agent operation: `timestamp · agent · transaction_id · outcome`.
6. **Reject/flag are outcomes, not errors.** A bad transaction produces a `rejected`/`flagged` envelope; it must not raise or abort the batch.

---

## 4. Agent contract (the three pipeline agents)

Each agent exposes `process_message(message: dict) -> dict` and:

- **reads** the standard envelope (§4 of the spec), **never** mutates the caller's dict in place beyond the documented enrichment;
- **enriches** `data` with its outcome (`status`, plus `reason` / `risk_*` / `settlement`);
- **passes through** envelopes whose `status` is already `rejected` (don't re-process a dead transaction);
- is a **pure function** w.r.t. IO — the **integrator** owns all file reads/writes and directory moves.

Stage order is fixed: `transaction_validator → fraud_detector → settlement_processor`.

---

## 5. Code style

- Pure logic in `agents/`; all IO (file moves, reads, writes) in `integrator.py` and `mcp/server.py`.
- Named functions, snake_case; module-level constants `SCREAMING_SNAKE_CASE` (e.g. `ISO_4217`, `HIGH_VALUE_THRESHOLD`).
- Comments explain **why**, not **what**. No dead code or commented-out blocks.
- One responsibility per file. No future-proofing beyond the spec.
- Thresholds (`10000`, `0.001`, score weights) are named constants, not magic numbers inline.

---

## 6. Testing expectations

Per `specification.md` §2 objectives:

| Type | Where | Covers |
|---|---|---|
| **Unit** | `tests/test_validator.py` | required fields, positive amount, ISO 4217 (incl. `XYZ` reject, negative amount) |
| **Unit** | `tests/test_fraud_detector.py` | high-value, cross-border, off-hours scoring; pass-through of rejected |
| **Unit** | `tests/test_settlement.py` | `ROUND_HALF_UP`, JPY 0dp, fee math; flagged/rejected not settled |
| **Integration** | `tests/test_pipeline.py` | full `run_pipeline` over a fixture; all inputs land in results |

- **Isolate from real `shared/`** — use `tmp_path`. Never write to the repo's `shared/` from tests.
- Coverage **gate is 80%** (hook blocks push below it); **aim ≥ 90%**.
- Tests are deterministic: no wall-clock, no randomness, no network.

---

## 7. Security & audit defaults

- No account number, name, or description in any log line, error message, or committed fixture beyond the provided sample.
- The MCP server is **read-only** over `shared/results/`; it never mutates pipeline state.
- No secrets in source. If asked to add one, refuse and propose an env var.
- Don't bypass the coverage hook with `--no-verify`.

---

## 8. When to ask the user

- A spec value needed for a decision is missing (e.g. a new currency, a changed threshold).
- A request contradicts a §3 rule (e.g. "just use float", "log the account number").
- A request to weaken or skip the coverage gate "to ship faster".

The cost of pausing is small; the cost of guessing in a money path is large.

---

## 9. What the agent must not do

- Use `float` for any monetary value, anywhere — including tests and fixtures.
- Log or echo `source_account` / `destination_account` / `description` in plaintext.
- Let one bad transaction throw and abort the batch.
- Add a dependency or a framework the spec doesn't call for.
- Bypass hooks/CI with flags like `--no-verify`.
