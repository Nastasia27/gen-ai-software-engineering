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


def test_off_hours_true_in_window():
    assert fd._off_hours("2026-03-16T02:47:00Z") is True


def test_off_hours_false_during_day():
    assert fd._off_hours("2026-03-16T09:00:00Z") is False


def test_off_hours_false_for_malformed_timestamp():
    assert fd._off_hours("not-a-timestamp") is False


def test_off_hours_false_for_none():
    assert fd._off_hours(None) is False


# --- score -------------------------------------------------------------------


def test_score_low_risk_clean_transaction():
    points, level, reasons = fd.score(_txn("1500.00"))
    assert points == 0
    assert level == "low"
    assert reasons == []


def test_score_high_value_is_medium():
    points, level, reasons = fd.score(_txn("25000.00"))
    assert points == 40
    assert level == "medium"
    assert "high_value" in reasons


def test_score_very_high_value_stacks_to_high():
    points, level, reasons = fd.score(_txn("75000.00"))
    assert points == 70  # high_value(40) + very_high_value(30)
    assert level == "high"
    assert "very_high_value" in reasons


def test_score_cross_border_adds_weight():
    points, _level, reasons = fd.score(_txn("500.00", country="DE"))
    assert points == 25
    assert "cross_border" in reasons


def test_score_off_hours_adds_weight():
    points, _level, reasons = fd.score(_txn("500.00", timestamp="2026-03-16T02:00:00Z"))
    assert points == 15
    assert "off_hours" in reasons


def test_score_defaults_country_to_home_when_metadata_absent():
    txn = {"transaction_id": "T", "amount": "500.00", "timestamp": "2026-03-16T09:00:00Z"}
    points, _level, reasons = fd.score(txn)
    assert "cross_border" not in reasons
    assert points == 0


# --- process_message ---------------------------------------------------------


def test_process_message_flags_high_risk():
    msg = {"data": _txn("75000.00")}
    out = fd.process_message(msg)
    assert out["data"]["status"] == "flagged"
    assert out["data"]["risk_level"] == "high"
    assert out["data"]["risk_score"] == 70
    assert out["source_agent"] == "fraud_detector"
    assert out["target_agent"] == "settlement_processor"


def test_process_message_approves_low_risk():
    msg = {"data": _txn("1500.00")}
    out = fd.process_message(msg)
    assert out["data"]["status"] == "approved"
    assert out["data"]["risk_level"] == "low"


def test_process_message_passes_through_rejected():
    msg = {"data": {"transaction_id": "TXN006", "status": "rejected", "reason": "invalid_currency:XYZ"}}
    out = fd.process_message(msg)
    assert out["data"]["status"] == "rejected"
    assert "risk_score" not in out["data"]  # never scored
