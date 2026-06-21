"""Integration tests for the pipeline orchestrator (integrator.py).

Every test writes into a per-test ``tmp_path`` so the real ``shared/`` tree is
never touched (TASK_LIST Етап 5: isolate tests from real shared/).
"""

import json

import pytest

import integrator


@pytest.fixture
def sample_transactions():
    return json.loads(integrator.SAMPLE_FILE.read_text(encoding="utf-8"))


# --- ensure_shared -----------------------------------------------------------


def test_ensure_shared_creates_all_four_dirs(tmp_path):
    integrator.ensure_shared(tmp_path)
    for name in integrator.SHARED_DIRS:
        assert (tmp_path / name).is_dir()


def test_ensure_shared_is_idempotent(tmp_path):
    integrator.ensure_shared(tmp_path)
    integrator.ensure_shared(tmp_path)  # must not raise on existing dirs
    assert (tmp_path / "results").is_dir()


# --- process_one -------------------------------------------------------------


def test_process_one_writes_file_at_each_stage(tmp_path):
    integrator.ensure_shared(tmp_path)
    txn = {
        "transaction_id": "TXN001", "amount": "1500.00", "currency": "USD",
        "source_account": "ACC-1001", "destination_account": "ACC-2001",
        "timestamp": "2026-03-16T09:00:00Z", "metadata": {"country": "US"},
    }
    result = integrator.process_one(txn, tmp_path)

    assert result["data"]["status"] == "settled"
    for stage in integrator.SHARED_DIRS:
        assert (tmp_path / stage / "TXN001.json").is_file()


# --- run_pipeline (full sample) ----------------------------------------------


def test_run_pipeline_tally_matches_expected_outcomes(tmp_path, sample_transactions):
    summary = integrator.run_pipeline(sample_transactions, tmp_path)

    assert summary["tally"] == {
        "total": 8,
        "validated": 6,
        "rejected": 2,
        "flagged": 1,
        "settled": 5,
    }


def test_run_pipeline_records_rejection_reasons(tmp_path, sample_transactions):
    summary = integrator.run_pipeline(sample_transactions, tmp_path)
    rejected_ids = {r["transaction_id"] for r in summary["rejections"]}
    assert rejected_ids == {"TXN006", "TXN007"}


def test_run_pipeline_writes_a_result_file_per_transaction(tmp_path, sample_transactions):
    integrator.run_pipeline(sample_transactions, tmp_path)
    results_dir = tmp_path / "results"
    for txn in sample_transactions:
        assert (results_dir / f"{txn['transaction_id']}.json").is_file()
    assert (results_dir / "_summary.json").is_file()


def test_run_pipeline_does_not_touch_real_shared(tmp_path, sample_transactions):
    real_shared = integrator.REPO_ROOT / "shared" / "results"
    before = set(real_shared.glob("*.json")) if real_shared.exists() else set()
    integrator.run_pipeline(sample_transactions, tmp_path)
    after = set(real_shared.glob("*.json")) if real_shared.exists() else set()
    assert before == after  # the run wrote only into tmp_path


# --- _print_summary ----------------------------------------------------------


def test_print_summary_includes_rejections(capsys):
    summary = {
        "tally": {"total": 1, "validated": 0, "rejected": 1, "flagged": 0, "settled": 0},
        "rejections": [{"transaction_id": "TXN006", "reason": "invalid_currency:XYZ"}],
        "transactions": [{"transaction_id": "TXN006", "final_status": "rejected", "risk_level": None}],
    }
    integrator._print_summary(summary)
    out = capsys.readouterr().out
    assert "Pipeline summary" in out
    assert "TXN006" in out
    assert "invalid_currency:XYZ" in out
    assert "risk=-" in out  # None risk_level renders as a dash


# --- main --------------------------------------------------------------------


def test_main_runs_end_to_end_in_isolated_tmp(tmp_path, monkeypatch, capsys):
    # Redirect both the sample source and the shared/ root into tmp_path.
    sample_copy = tmp_path / "sample-transactions.json"
    sample_copy.write_text(integrator.SAMPLE_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(integrator, "SAMPLE_FILE", sample_copy)
    monkeypatch.setattr(integrator, "REPO_ROOT", tmp_path)

    rc = integrator.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert "Pipeline summary" in out
    assert (tmp_path / "shared" / "results" / "_summary.json").is_file()
