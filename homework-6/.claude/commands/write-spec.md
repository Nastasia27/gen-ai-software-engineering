---
name: write-spec
description: Generate a project specification.md for the multi-agent banking pipeline, following the required 5-section template (High-Level, Mid-Level, Implementation Notes, Context, Low-Level Tasks per agent).
---

# /write-spec — Generate the project specification

You are **Agent 1 (Specification)** for Homework 6. Produce a complete `specification.md`
for a file-based multi-agent banking transaction pipeline, following the exact template below.

## Inputs to read first
1. `sample-transactions.json` — understand the real input shape and the deliberate edge cases
   (non-ISO currency, negative amount, high-value wires, off-hours cross-border). The spec's
   rules must be justified by this data.
2. `agents.md` — the domain rules the spec must stay consistent with (Decimal money, ISO 4217,
   PII masking, UTC timing, audit trail).

## Output
Write/overwrite `specification.md` with these **5 sections, in order**:

1. **High-Level Objective** — exactly one sentence describing what the pipeline does.
2. **Mid-Level Objectives** — 4–5 concrete, testable requirements. Each must be checkable by a unit
   test. Cover: validation gate, fraud risk scoring (threshold $10,000), deterministic settlement,
   file-based hand-off, and audit logging.
3. **Implementation Notes** — money is `decimal.Decimal` (never float); ISO 4217 currency allow-list;
   audit log = timestamp + agent + transaction_id + outcome; PII (account numbers, names, description)
   masked, never logged in plaintext; timing read from the transaction's own timestamp (no wall-clock).
4. **Context** — Beginning state (`sample-transactions.json`, empty `shared/` dirs) and Ending state
   (results in `shared/results/`, `_summary.json`, MCP server, tests ≥ 90% coverage). Include the
   standard JSON message envelope.
5. **Low-Level Tasks** — **one entry per agent**, each in this format:
   ```
   Task: [Agent Name]
   Prompt: "[Exact prompt to give the code-gen agent]"
   File to CREATE: agents/<name>.py
   Function to CREATE: process_message(message: dict) -> dict
   Details: [what the agent checks, transforms, or decides]
   ```
   Cover at minimum: Transaction Validator, Fraud Detector, a third agent (Settlement Processor),
   the Integrator, and the MCP server.

## Rules
- Keep it consistent with `agents.md`; if you introduce a new rule, it must not contradict it.
- Be specific and testable — vague objectives ("handle errors well") are rejected.
- Name concrete thresholds and constants ($10,000 fraud flag, 0.1% fee, ROUND_HALF_UP, JPY 0dp).
- Include the author line: **Anastasia Kopiika**.
- Do not write pipeline code — only the specification.
