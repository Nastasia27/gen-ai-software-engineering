# Multi-Agent Banking Transaction Pipeline — Specification

> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.
>
> **Author:** Anastasia Kopiika · **Stack:** Python 3.10+ (stdlib `decimal`, `json`, `uuid`, `logging`), FastMCP, pytest + pytest-cov.

---

## 1. High-Level Objective

Build a file-based multi-agent pipeline that ingests raw bank transactions, validates them, scores them for fraud risk, settles the approved ones, and writes an auditable result for every transaction to `shared/results/`.

---

## 2. Mid-Level Objectives

1. **Validation gate** — every transaction is checked for required fields, a positive monetary amount, and a valid ISO 4217 currency; failures are rejected with a machine-readable `reason` and never reach later stages.
2. **Risk scoring** — transactions are assigned a `risk_score` (0–100) and `risk_level`; amounts above **$10,000**, cross-border transfers, and activity between 00:00–05:00 UTC raise the score, and high-risk transactions are flagged for review rather than auto-settled.
3. **Deterministic settlement** — approved transactions compute a net settlement amount using `decimal.Decimal` with `ROUND_HALF_UP`, never floating point.
4. **File-based hand-off** — agents communicate only through JSON message files moving across `shared/{input,processing,output,results}/`, each message carrying `message_id`, `timestamp`, `source_agent`, and `target_agent`.
5. **Audit trail** — every agent operation is logged with an ISO 8601 timestamp, agent name, transaction ID, and outcome; account numbers and descriptions (PII) are masked in logs.

---

## 3. Implementation Notes

- **Money:** all amounts parsed and computed with `decimal.Decimal` — never `float`. Settlement rounding uses `ROUND_HALF_UP` at 2 decimal places.
- **Currency:** validated against an explicit ISO 4217 allow-list (`USD, EUR, GBP, JPY, CHF, CAD, AUD`). `JPY` is recognized as a zero-decimal currency.
- **Logging:** one structured audit line per operation — `timestamp · agent · transaction_id · outcome`. PII (`source_account`, `destination_account`, `description`) is masked (e.g. `ACC-1001` → `ACC-****`); amounts and currency may be logged.
- **Messages:** the canonical envelope is defined in §4; agents read from one `shared/` stage and write the enriched envelope to the next. Status flows `validated → scored → settled`/`rejected`/`flagged`.
- **Determinism:** no `datetime.now()` / randomness inside agent decision logic — timing checks read the transaction's own `timestamp`. This keeps the suite repeatable.
- **Failure isolation:** a rejection or flag is a normal outcome, not an exception. Unhandled exceptions in one transaction must not abort the batch.

---

## 4. Context

### Beginning context
- `sample-transactions.json` — 8 raw transaction records (includes deliberate edge cases: a non-ISO currency `XYZ`, a negative amount, two high-value wires, and an off-hours cross-border transfer).
- Empty `shared/{input,processing,output,results}/` directories.
- `specification.md`, `agents.md` (this stage).

### Ending context
- `agents/transaction_validator.py`, `agents/fraud_detector.py`, `agents/settlement_processor.py` — three cooperating agents.
- `integrator.py` — orchestrator that seeds `shared/input/`, runs the agents in order, and collects results.
- One result JSON per transaction in `shared/results/` and a `shared/results/_summary.json` pipeline report.
- `mcp/server.py` (FastMCP) exposing pipeline status as tools + a resource.
- `tests/` with per-agent unit tests + one integration test; coverage ≥ 90%.
- `README.md`, `HOWTORUN.md`, `research-notes.md`, and screenshots in `docs/screenshots/`.

### Message envelope (standard format)
```json
{
  "message_id": "uuid4-string",
  "timestamp": "2026-03-16T10:00:00Z",
  "source_agent": "transaction_validator",
  "target_agent": "fraud_detector",
  "message_type": "transaction",
  "data": {
    "transaction_id": "TXN001",
    "amount": "1500.00",
    "currency": "USD",
    "status": "validated"
  }
}
```

---

## 5. Low-Level Tasks

### Task: Transaction Validator
```
Prompt: "Create a Transaction Validator agent. Read a transaction message envelope, check that all
required fields are present (transaction_id, amount, currency, source_account, destination_account,
timestamp), that the amount parses as a positive decimal.Decimal, and that the currency is in the
ISO 4217 allow-list. Return the envelope with data.status set to 'validated' or 'rejected' plus a
'reason' on failure. Mask account numbers in audit logs."
File to CREATE: agents/transaction_validator.py
Function to CREATE: process_message(message: dict) -> dict
Details:
  - Required fields list; missing/empty field → status 'rejected', reason 'missing_field:<name>'.
  - amount: Decimal(str(amount)) must be > 0; non-numeric → 'invalid_amount'; <= 0 → 'non_positive_amount'.
  - currency: uppercase membership test against ISO_4217 allow-list; miss → 'invalid_currency:<code>'.
  - Supports --dry-run CLI mode: read sample-transactions.json, print total/valid/invalid + reasons table.
  - Never raises on a bad record; converts the failure into a rejected envelope.
```

### Task: Fraud Detector
```
Prompt: "Create a Fraud Detector agent that consumes validated transaction envelopes and assigns a
risk_score (0-100) and risk_level (low/medium/high). Raise score for amount > 10000, cross-border
(metadata.country != home country US), and off-hours timing (00:00-05:00 UTC from the transaction's
own timestamp). Flag high-risk (score >= 70) for manual review; otherwise mark approved."
File to CREATE: agents/fraud_detector.py
Function to CREATE: process_message(message: dict) -> dict
Details:
  - Additive rules: +40 amount > 10000, +30 amount > 50000 (stacks -> 70 = high), +25 cross-border, +15 off-hours.
  - Clamp score to 0-100. risk_level: <30 low, 30-69 medium, >=70 high.
  - status: 'flagged' if high else 'approved'; attach risk_score, risk_level, risk_reasons[].
  - Timing read from data/transaction timestamp (parse hour) — no wall-clock calls (keeps tests repeatable).
  - Reject envelopes (status 'rejected') pass through untouched.
```

### Task: Settlement Processor
```
Prompt: "Create a Settlement Processor agent that finalizes approved transactions. Compute a net
settlement amount from the gross amount minus a fee, using decimal.Decimal with ROUND_HALF_UP at 2dp
(0dp for JPY). Write the final outcome. Flagged and rejected transactions are recorded without settling."
File to CREATE: agents/settlement_processor.py
Function to CREATE: process_message(message: dict) -> dict
Details:
  - fee = gross * Decimal('0.001') (0.1%), quantized ROUND_HALF_UP; net = gross - fee.
  - JPY quantizes to 0 decimal places; all others to 2.
  - status 'approved' -> 'settled' with settlement{gross,fee,net,currency}; 'flagged'/'rejected' kept as-is.
  - Pure function: no IO inside process_message; the integrator handles file writes.
```

### Task: Integrator / Orchestrator
```
Prompt: "Create the pipeline orchestrator. Ensure shared/ dirs exist, load sample-transactions.json,
wrap each record in a message envelope, then run it through validator -> fraud_detector ->
settlement_processor, moving the JSON file across shared/input -> processing -> output -> results.
Write one result file per transaction plus shared/results/_summary.json. Print a human summary."
File to CREATE: integrator.py
Function to CREATE: run_pipeline(transactions: list[dict], shared_dir: Path) -> dict
Details:
  - Stage hand-off writes the envelope at each shared/ subdir so the file-based protocol is observable.
  - Aggregate counts: total, validated, rejected, flagged, settled; list rejection/flag reasons.
  - _summary.json holds the aggregate + per-transaction (transaction_id, final_status, risk_level).
  - Audit-log every stage transition. Returns the summary dict for tests/MCP to consume.
```

### Task: Pipeline Status MCP Server
```
Prompt: "Create a FastMCP server exposing the pipeline results. Tool get_transaction_status(transaction_id)
reads shared/results/ and returns the stored outcome; tool list_pipeline_results() returns a summary of
all processed transactions; resource pipeline://summary returns the latest _summary.json as text."
File to CREATE: mcp/server.py
Function to CREATE: get_transaction_status / list_pipeline_results / pipeline_summary
Details:
  - Read-only over shared/results/; resolve paths relative to the repo root, not cwd.
  - Unknown transaction_id -> structured 'not_found' result, never an exception.
  - Reuse the same JSON the integrator writes; no separate datastore.
```
