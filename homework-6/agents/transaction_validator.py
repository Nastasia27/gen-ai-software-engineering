"""Agent 1 of the pipeline: Transaction Validator.

Checks required fields, a positive monetary amount, and a valid ISO 4217
currency. Produces a 'validated' or 'rejected' envelope — never raises on a bad
record (a rejection is a normal outcome, see agents.md §3).
"""

from __future__ import annotations

# Allow running this file directly (python agents/transaction_validator.py --dry-run)
# by putting the repo root on sys.path before the package import resolves.
if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.common import (
    ISO_4217,
    REQUIRED_FIELDS,
    InvalidOperation,
    audit,
    mask_account,
    parse_amount,
)

AGENT_NAME = "transaction_validator"


def validate(transaction: dict) -> tuple[bool, str | None]:
    """Return (is_valid, reason). ``reason`` is None when valid."""
    for field in REQUIRED_FIELDS:
        value = transaction.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return False, f"missing_field:{field}"

    try:
        amount = parse_amount(transaction["amount"])
    except (InvalidOperation, ValueError, TypeError):
        return False, "invalid_amount"
    if amount <= 0:
        return False, "non_positive_amount"

    currency = str(transaction["currency"]).upper()
    if currency not in ISO_4217:
        return False, f"invalid_currency:{currency}"

    return True, None


def process_message(message: dict) -> dict:
    """Enrich the envelope's data with a 'validated' or 'rejected' status."""
    data = message.setdefault("data", {})
    transaction_id = data.get("transaction_id", "UNKNOWN")

    ok, reason = validate(data)
    if ok:
        data["status"] = "validated"
        audit(AGENT_NAME, transaction_id, "validated")
    else:
        data["status"] = "rejected"
        data["reason"] = reason
        audit(AGENT_NAME, transaction_id, f"rejected:{reason}")

    message["source_agent"] = AGENT_NAME
    message["target_agent"] = "fraud_detector"
    return message


# --- CLI: dry-run validation over sample-transactions.json -------------------


def _dry_run() -> int:
    """Validate every transaction in the sample file and print a report."""
    import json
    from pathlib import Path

    sample = Path(__file__).resolve().parents[1] / "sample-transactions.json"
    transactions = json.loads(sample.read_text(encoding="utf-8"))

    rows, valid_count = [], 0
    for txn in transactions:
        ok, reason = validate(txn)
        valid_count += ok
        rows.append((txn.get("transaction_id", "UNKNOWN"), mask_account(txn.get("source_account", "")),
                     "VALID" if ok else "INVALID", reason or "-"))

    total = len(transactions)
    print(f"Validation dry-run: {total} total · {valid_count} valid · {total - valid_count} invalid\n")
    print(f"{'TXN':<10}{'SOURCE':<12}{'RESULT':<10}REASON")
    print("-" * 50)
    for txn_id, source, result, reason in rows:
        print(f"{txn_id:<10}{source:<12}{result:<10}{reason}")
    return 0


if __name__ == "__main__":
    import sys

    if "--dry-run" in sys.argv:
        raise SystemExit(_dry_run())
    print("Usage: python agents/transaction_validator.py --dry-run")
