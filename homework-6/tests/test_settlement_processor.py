"""Unit tests for agents.settlement_processor (Agent 3)."""

from agents import settlement_processor as sp


# --- settle ------------------------------------------------------------------


def test_settle_usd_applies_tenth_percent_fee():
    out = sp.settle({"amount": "25000.00", "currency": "USD"})
    assert out == {"gross": "25000.00", "fee": "25.00", "net": "24975.00", "currency": "USD"}


def test_settle_jpy_uses_zero_decimals():
    out = sp.settle({"amount": "100000", "currency": "JPY"})
    assert out["currency"] == "JPY"
    assert out["gross"] == "100000"
    assert out["fee"] == "100"  # 0.1% of 100000, 0dp
    assert out["net"] == "99900"


def test_settle_normalizes_currency_case():
    out = sp.settle({"amount": "1000.00", "currency": "usd"})
    assert out["currency"] == "USD"


# --- process_message ---------------------------------------------------------


def test_process_message_settles_approved():
    msg = {"data": {"transaction_id": "TXN001", "amount": "1500.00", "currency": "USD", "status": "approved"}}
    out = sp.process_message(msg)
    assert out["data"]["status"] == "settled"
    assert out["data"]["settlement"]["net"] == "1498.50"
    assert out["source_agent"] == "settlement_processor"
    assert out["target_agent"] == "results"


def test_process_message_leaves_flagged_unsettled():
    msg = {"data": {"transaction_id": "TXN005", "amount": "75000.00", "currency": "USD", "status": "flagged"}}
    out = sp.process_message(msg)
    assert out["data"]["status"] == "flagged"
    assert "settlement" not in out["data"]


def test_process_message_leaves_rejected_unsettled():
    msg = {"data": {"transaction_id": "TXN006", "status": "rejected"}}
    out = sp.process_message(msg)
    assert out["data"]["status"] == "rejected"
    assert "settlement" not in out["data"]
