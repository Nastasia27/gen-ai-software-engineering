"""Shared helpers for the multi-agent banking pipeline.

Pure domain constants and small utilities used by every agent. No file IO lives
here — agents stay pure and the integrator owns reads/writes (see agents.md §4).
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal, InvalidOperation

# --- Domain constants --------------------------------------------------------

# ISO 4217 currencies this pipeline accepts. Anything else is rejected.
ISO_4217 = {"USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"}

# Zero-decimal currencies settle to whole units (no minor unit).
ZERO_DECIMAL_CURRENCIES = {"JPY"}

REQUIRED_FIELDS = (
    "transaction_id",
    "amount",
    "currency",
    "source_account",
    "destination_account",
    "timestamp",
)

# Fraud thresholds / weights (see specification.md §5, Fraud Detector).
HIGH_VALUE_THRESHOLD = Decimal("10000")
VERY_HIGH_VALUE_THRESHOLD = Decimal("50000")
HOME_COUNTRY = "US"
OFF_HOURS_START = 0   # 00:00 UTC inclusive
OFF_HOURS_END = 5     # 05:00 UTC exclusive
HIGH_RISK_SCORE = 70

# Settlement fee: 0.1% of gross.
FEE_RATE = Decimal("0.001")

# Fields treated as PII — never logged in plaintext.
PII_FIELDS = ("source_account", "destination_account", "description")

# --- Logging / audit trail ---------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s · %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
_logger = logging.getLogger("pipeline")


def mask_account(value: str) -> str:
    """Mask a sensitive identifier for logs: ``ACC-1001`` -> ``ACC-****``."""
    if not value:
        return "****"
    return value[:4] + "****" if len(value) > 4 else "****"


def audit(agent: str, transaction_id: str, outcome: str) -> None:
    """Write one audit line: timestamp (from the log formatter) · agent · txn · outcome."""
    _logger.info("%s · %s · %s", agent, transaction_id, outcome)


# --- Money / parsing helpers -------------------------------------------------


def parse_amount(raw) -> Decimal:
    """Parse a monetary value to ``Decimal`` from a string/number.

    Raises ``InvalidOperation`` for non-numeric input so callers can reject it.
    """
    return Decimal(str(raw))


def quantize_money(amount: Decimal, currency: str) -> Decimal:
    """Round to the currency's minor unit (0dp for JPY, else 2dp), ROUND_HALF_UP."""
    from decimal import ROUND_HALF_UP

    exponent = Decimal("1") if currency in ZERO_DECIMAL_CURRENCIES else Decimal("0.01")
    return amount.quantize(exponent, rounding=ROUND_HALF_UP)


# --- Message envelope --------------------------------------------------------


def new_envelope(transaction: dict, source_agent: str, target_agent: str) -> dict:
    """Wrap a raw transaction in the standard message envelope (specification.md §4).

    The envelope timestamp is taken from the transaction itself to keep the
    pipeline deterministic (no wall-clock in the data path).
    """
    data = dict(transaction)
    data.setdefault("status", "received")
    return {
        "message_id": str(uuid.uuid4()),
        "timestamp": transaction.get("timestamp"),
        "source_agent": source_agent,
        "target_agent": target_agent,
        "message_type": "transaction",
        "data": data,
    }


def is_dead(message: dict) -> bool:
    """True if the transaction was already rejected and must not be re-processed."""
    return message.get("data", {}).get("status") == "rejected"


__all__ = [
    "ISO_4217",
    "ZERO_DECIMAL_CURRENCIES",
    "REQUIRED_FIELDS",
    "HIGH_VALUE_THRESHOLD",
    "VERY_HIGH_VALUE_THRESHOLD",
    "HOME_COUNTRY",
    "HIGH_RISK_SCORE",
    "FEE_RATE",
    "PII_FIELDS",
    "InvalidOperation",
    "mask_account",
    "audit",
    "parse_amount",
    "quantize_money",
    "new_envelope",
    "is_dead",
]
