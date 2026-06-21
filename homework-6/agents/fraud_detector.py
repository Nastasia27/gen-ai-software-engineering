"""Agent 2 of the pipeline: Fraud Detector.

Scores validated transactions for risk and flags high-risk ones for manual
review. Timing is read from the transaction's own timestamp (never the wall
clock) so the scoring is deterministic and testable (agents.md §3.4).
"""

from __future__ import annotations

from agents.common import (
    HIGH_RISK_SCORE,
    HIGH_VALUE_THRESHOLD,
    HOME_COUNTRY,
    VERY_HIGH_VALUE_THRESHOLD,
    audit,
    is_dead,
    parse_amount,
)

AGENT_NAME = "fraud_detector"

# Additive risk weights.
W_HIGH_VALUE = 40
W_VERY_HIGH_VALUE = 30  # stacks on high-value: >$50k => 70 => high-risk => flagged
W_CROSS_BORDER = 25
W_OFF_HOURS = 15


def _off_hours(timestamp: str) -> bool:
    """True if the transaction hour (UTC) falls in 00:00–05:00."""
    # Expecting ISO 8601 like '2026-03-16T02:47:00Z'.
    try:
        hour = int(timestamp.split("T", 1)[1][:2])
    except (AttributeError, IndexError, ValueError):
        return False
    return 0 <= hour < 5


def score(transaction: dict) -> tuple[int, str, list[str]]:
    """Return (risk_score 0–100, risk_level, reasons)."""
    points = 0
    reasons: list[str] = []

    amount = parse_amount(transaction["amount"])
    if amount > HIGH_VALUE_THRESHOLD:
        points += W_HIGH_VALUE
        reasons.append("high_value")
    if amount > VERY_HIGH_VALUE_THRESHOLD:
        points += W_VERY_HIGH_VALUE
        reasons.append("very_high_value")

    country = transaction.get("metadata", {}).get("country", HOME_COUNTRY)
    if country != HOME_COUNTRY:
        points += W_CROSS_BORDER
        reasons.append("cross_border")

    if _off_hours(transaction.get("timestamp", "")):
        points += W_OFF_HOURS
        reasons.append("off_hours")

    points = max(0, min(100, points))
    if points >= HIGH_RISK_SCORE:
        level = "high"
    elif points >= 30:
        level = "medium"
    else:
        level = "low"
    return points, level, reasons


def process_message(message: dict) -> dict:
    """Attach risk_score/risk_level and set status to 'approved' or 'flagged'."""
    message["source_agent"] = AGENT_NAME
    message["target_agent"] = "settlement_processor"

    if is_dead(message):
        return message  # already rejected upstream — pass through untouched

    data = message["data"]
    transaction_id = data.get("transaction_id", "UNKNOWN")

    risk_score, risk_level, reasons = score(data)
    data["risk_score"] = risk_score
    data["risk_level"] = risk_level
    data["risk_reasons"] = reasons

    if risk_score >= HIGH_RISK_SCORE:
        data["status"] = "flagged"
        audit(AGENT_NAME, transaction_id, f"flagged:{risk_score}:{','.join(reasons)}")
    else:
        data["status"] = "approved"
        audit(AGENT_NAME, transaction_id, f"approved:{risk_score}")
    return message
