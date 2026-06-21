---
name: validate-transactions
description: Validate all transactions in sample-transactions.json without running the full pipeline (dry-run).
---

# /validate-transactions — Validate without processing

Validate all transactions in `sample-transactions.json` without processing them.

Steps:
1. Run the validator in dry-run mode: `python3 agents/transaction_validator.py --dry-run`
2. Report: total count, valid count, invalid count, and the reason for each rejection
   (e.g. `invalid_currency:XYZ`, `non_positive_amount`, `missing_field:<name>`).
3. Show the results as a table (TXN · source · VALID/INVALID · reason). The dry-run already prints
   this table — surface it to the user and summarize the takeaway (which transactions fail and why).

Note: this does **not** touch `shared/` and does **not** run fraud scoring or settlement — it only
exercises the validation gate.
