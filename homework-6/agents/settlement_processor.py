"""Agent 3 of the pipeline: Settlement Processor.

Finalizes approved transactions by computing a net settlement amount
(gross − 0.1% fee) using Decimal with ROUND_HALF_UP (0dp for JPY). Flagged and
rejected transactions are recorded as-is and never settled.
"""

from __future__ import annotations

from agents.common import (
    FEE_RATE,
    audit,
    parse_amount,
    quantize_money,
)

AGENT_NAME = "settlement_processor"


def settle(transaction: dict) -> dict:
    """Compute settlement breakdown for an approved transaction."""
    currency = str(transaction["currency"]).upper()
    gross = quantize_money(parse_amount(transaction["amount"]), currency)
    fee = quantize_money(gross * FEE_RATE, currency)
    net = quantize_money(gross - fee, currency)
    return {
        "gross": str(gross),
        "fee": str(fee),
        "net": str(net),
        "currency": currency,
    }


def process_message(message: dict) -> dict:
    """Settle approved transactions; leave flagged/rejected as final outcomes."""
    message["source_agent"] = AGENT_NAME
    message["target_agent"] = "results"

    data = message["data"]
    transaction_id = data.get("transaction_id", "UNKNOWN")
    status = data.get("status")

    if status == "approved":
        data["settlement"] = settle(data)
        data["status"] = "settled"
        audit(AGENT_NAME, transaction_id, f"settled:net={data['settlement']['net']}")
    else:
        # 'flagged' or 'rejected' — terminal, recorded without settlement.
        audit(AGENT_NAME, transaction_id, f"not_settled:{status}")
    return message
