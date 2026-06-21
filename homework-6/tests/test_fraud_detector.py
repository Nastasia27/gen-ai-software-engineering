"""Unit tests for agents.fraud_detector (Agent 2)."""

from agents import fraud_detector as fd


def _txn(amount, country="US", timestamp="2026-03-16T09:00:00Z"):
    return {
        "transaction_id": "TXN",
        "amount": amount,
        "currency": "USD",
        "timestamp": timestamp,
        "metadata": {"country": country},
    }


# --- _off_hours --------------------------------------------------------------

