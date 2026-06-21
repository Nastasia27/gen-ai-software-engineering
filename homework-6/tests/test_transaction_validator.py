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


def test_validate_accepts_well_formed_transaction():
    assert tv.validate(_valid_txn()) == (True, None)


def test_validate_lowercase_currency_is_normalized():
    ok, reason = tv.validate(_valid_txn(currency="usd"))
    assert ok is True and reason is None


@pytest.mark.parametrize("field", [
    "transaction_id", "amount", "currency",
    "source_account", "destination_account", "timestamp",
])
def test_validate_rejects_missing_field(field):
    txn = _valid_txn()
    del txn[field]
    ok, reason = tv.validate(txn)
    assert ok is False
    assert reason == f"missing_field:{field}"


def test_validate_rejects_blank_string_field():
    ok, reason = tv.validate(_valid_txn(source_account="   "))
    assert ok is False
    assert reason == "missing_field:source_account"


def test_validate_rejects_non_numeric_amount():
    ok, reason = tv.validate(_valid_txn(amount="abc"))
    assert (ok, reason) == (False, "invalid_amount")


def test_validate_rejects_non_positive_amount():
    ok, reason = tv.validate(_valid_txn(amount="-100.00"))
    assert (ok, reason) == (False, "non_positive_amount")


def test_validate_rejects_zero_amount():
    ok, reason = tv.validate(_valid_txn(amount="0"))
    assert (ok, reason) == (False, "non_positive_amount")


def test_validate_rejects_unknown_currency():
    ok, reason = tv.validate(_valid_txn(currency="XYZ"))
    assert (ok, reason) == (False, "invalid_currency:XYZ")


# --- process_message ---------------------------------------------------------


def test_process_message_marks_valid_transaction_validated():
    msg = {"data": _valid_txn()}
    out = tv.process_message(msg)
    assert out["data"]["status"] == "validated"
    assert out["source_agent"] == "transaction_validator"
    assert out["target_agent"] == "fraud_detector"
    assert "reason" not in out["data"]


def test_process_message_rejects_and_records_reason():
    msg = {"data": _valid_txn(currency="XYZ")}
    out = tv.process_message(msg)
    assert out["data"]["status"] == "rejected"
    assert out["data"]["reason"] == "invalid_currency:XYZ"


def test_process_message_handles_missing_data_key():
    out = tv.process_message({})
    assert out["data"]["status"] == "rejected"


# --- CLI dry-run -------------------------------------------------------------


def test_dry_run_prints_report(capsys):
    rc = tv._dry_run()
    out = capsys.readouterr().out
    assert rc == 0
    assert "Validation dry-run" in out
    assert "TXN006" in out  # the XYZ currency row is present
