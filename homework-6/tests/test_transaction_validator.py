"""Unit tests for agents.transaction_validator (Agent 1)."""

import pytest

from agents import transaction_validator as tv


def _valid_txn(**overrides):
    txn = {
        "transaction_id": "TXN001",
        "amount": "1500.00",
        "currency": "USD",
        "source_account": "ACC-1001",
        "destination_account": "ACC-2001",
        "timestamp": "2026-03-16T09:00:00Z",
    }
    txn.update(overrides)
    return txn


# --- validate ----------------------------------------------------------------


