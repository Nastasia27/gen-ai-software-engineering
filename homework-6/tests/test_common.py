"""Unit tests for agents.common — domain constants and small helpers."""

from decimal import Decimal

import pytest

from agents import common


# --- mask_account ------------------------------------------------------------


def test_mask_account_long_value_keeps_prefix():
    assert common.mask_account("ACC-1001") == "ACC-****"


def test_mask_account_short_value_fully_masked():
    assert common.mask_account("AC") == "****"


def test_mask_account_empty_value_fully_masked():
    assert common.mask_account("") == "****"


# --- audit -------------------------------------------------------------------


def test_audit_emits_log_line_without_pii(caplog):
    import logging

    with caplog.at_level(logging.INFO, logger="pipeline"):
        common.audit("transaction_validator", "TXN001", "validated")
    assert "transaction_validator" in caplog.text
    assert "TXN001" in caplog.text


# --- parse_amount ------------------------------------------------------------


def test_parse_amount_from_string():
    assert common.parse_amount("1500.00") == Decimal("1500.00")


def test_parse_amount_from_number():
    assert common.parse_amount(42) == Decimal("42")


def test_parse_amount_invalid_raises():
    with pytest.raises(common.InvalidOperation):
        common.parse_amount("not-a-number")


# --- quantize_money ----------------------------------------------------------


def test_quantize_money_usd_two_decimals():
    assert common.quantize_money(Decimal("24.999"), "USD") == Decimal("25.00")


def test_quantize_money_jpy_zero_decimals():
    assert common.quantize_money(Decimal("100.6"), "JPY") == Decimal("101")


def test_quantize_money_rounds_half_up_not_bankers():
    # Banker's rounding would give 2.00; ROUND_HALF_UP must give 2.01.
    assert common.quantize_money(Decimal("2.005"), "USD") == Decimal("2.01")


# --- new_envelope ------------------------------------------------------------


def test_new_envelope_structure_and_defaults():
    txn = {"transaction_id": "TXN001", "timestamp": "2026-03-16T09:00:00Z"}
    env = common.new_envelope(txn, source_agent="integrator", target_agent="transaction_validator")

    assert env["message_type"] == "transaction"
    assert env["source_agent"] == "integrator"
    assert env["target_agent"] == "transaction_validator"
    assert env["timestamp"] == "2026-03-16T09:00:00Z"
    assert env["data"]["status"] == "received"  # default applied
    assert env["message_id"]  # a uuid was assigned


def test_new_envelope_does_not_mutate_caller_dict():
    txn = {"transaction_id": "TXN001", "timestamp": "t"}
    common.new_envelope(txn, "a", "b")
    assert "status" not in txn  # envelope copies the transaction


def test_new_envelope_keeps_existing_status():
    txn = {"transaction_id": "TXN001", "timestamp": "t", "status": "rejected"}
    env = common.new_envelope(txn, "a", "b")
    assert env["data"]["status"] == "rejected"


# --- is_dead -----------------------------------------------------------------


def test_is_dead_true_when_rejected():
    assert common.is_dead({"data": {"status": "rejected"}}) is True


def test_is_dead_false_for_other_status():
    assert common.is_dead({"data": {"status": "validated"}}) is False


def test_is_dead_false_when_no_data():
    assert common.is_dead({}) is False
