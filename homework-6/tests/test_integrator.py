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
