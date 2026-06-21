#!/usr/bin/env python3
"""Coverage gate: run the test suite with coverage and fail below the threshold.

Exit code 0 = coverage meets the gate; non-zero = below the gate (or no tests).
Used by both the Claude Code push hook and the git pre-push hook so the rule is
defined in exactly one place.
"""

import subprocess
import sys
from pathlib import Path

THRESHOLD = 80
PROJECT_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=agents", "--cov=integrator",
        "--cov-report=term-missing",
        f"--cov-fail-under={THRESHOLD}",
        "-q",
    ]
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    if result.returncode != 0:
        print(
            f"\n❌ Coverage gate FAILED — total coverage is below {THRESHOLD}%.",
            file=sys.stderr,
        )
        return 1
    print(f"\n✅ Coverage gate PASSED — coverage is at or above {THRESHOLD}%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
