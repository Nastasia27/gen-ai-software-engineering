"""Pipeline orchestrator (integrator).

Seeds ``shared/input/`` from ``sample-transactions.json``, then runs every
transaction through validator -> fraud_detector -> settlement_processor, moving
its JSON message across ``shared/{input,processing,output,results}/`` so the
file-based protocol is observable. Writes one result file per transaction plus
``shared/results/_summary.json`` and prints a human-readable summary.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents import fraud_detector, settlement_processor, transaction_validator
from agents.common import new_envelope

REPO_ROOT = Path(__file__).resolve().parent
SAMPLE_FILE = REPO_ROOT / "sample-transactions.json"
SHARED_DIRS = ("input", "processing", "output", "results")

# Final statuses, in stage order, for the summary tally.
STAGES = (transaction_validator, fraud_detector, settlement_processor)


def ensure_shared(shared_dir: Path) -> None:
    """Create the four shared/ subdirectories if they do not exist."""
    for name in SHARED_DIRS:
        (shared_dir / name).mkdir(parents=True, exist_ok=True)


def _write(path: Path, envelope: dict) -> None:
    path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")


def process_one(transaction: dict, shared_dir: Path) -> dict:
    """Run a single transaction through all stages, moving its file each step."""
    txn_id = transaction.get("transaction_id", "UNKNOWN")
    envelope = new_envelope(transaction, source_agent="integrator", target_agent="transaction_validator")

    # input -> processing -> output -> results, written at each hop.
    _write(shared_dir / "input" / f"{txn_id}.json", envelope)

    envelope = transaction_validator.process_message(envelope)
    _write(shared_dir / "processing" / f"{txn_id}.json", envelope)

    envelope = fraud_detector.process_message(envelope)
    envelope = settlement_processor.process_message(envelope)
    _write(shared_dir / "output" / f"{txn_id}.json", envelope)

    _write(shared_dir / "results" / f"{txn_id}.json", envelope)
    return envelope


def run_pipeline(transactions: list[dict], shared_dir: Path) -> dict:
    """Process every transaction and return an aggregate summary dict."""
    ensure_shared(shared_dir)

    tally = {"total": 0, "validated": 0, "rejected": 0, "flagged": 0, "settled": 0}
    rejections: list[dict] = []
    per_transaction: list[dict] = []

    for txn in transactions:
        result = process_one(txn, shared_dir)
        data = result["data"]
        status = data.get("status")

        tally["total"] += 1
        if status == "rejected":
            tally["rejected"] += 1
            rejections.append({"transaction_id": data.get("transaction_id"), "reason": data.get("reason")})
        else:
            tally["validated"] += 1  # passed the validation gate
            if status == "flagged":
                tally["flagged"] += 1
            elif status == "settled":
                tally["settled"] += 1

        per_transaction.append({
            "transaction_id": data.get("transaction_id"),
            "final_status": status,
            "risk_level": data.get("risk_level"),
        })

    summary = {"tally": tally, "rejections": rejections, "transactions": per_transaction}
    _write(shared_dir / "results" / "_summary.json", summary)
    return summary


def _print_summary(summary: dict) -> None:
    t = summary["tally"]
    print("\n=== Pipeline summary ===")
    print(f"Total: {t['total']} · Validated: {t['validated']} · Rejected: {t['rejected']} "
          f"· Flagged: {t['flagged']} · Settled: {t['settled']}")
    if summary["rejections"]:
        print("\nRejected transactions:")
        for r in summary["rejections"]:
            print(f"  - {r['transaction_id']}: {r['reason']}")
    print("\nPer-transaction outcomes:")
    for row in summary["transactions"]:
        risk = row["risk_level"] or "-"
        print(f"  {row['transaction_id']:<8} {row['final_status']:<10} risk={risk}")


def main() -> int:
    transactions = json.loads(SAMPLE_FILE.read_text(encoding="utf-8"))
    summary = run_pipeline(transactions, REPO_ROOT / "shared")
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
