#!/usr/bin/env python3
"""Claude Code PreToolUse hook: gate `git push` on test coverage.

Reads the tool-call JSON from stdin. If the Bash command is a `git push`, runs
the coverage gate; when coverage is below the threshold it exits with code 2,
which tells Claude Code to BLOCK the push. Any non-push command is allowed
through untouched (exit 0).
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # not a JSON tool call we understand — don't interfere

    command = payload.get("tool_input", {}).get("command", "")
    if "git push" not in command:
        return 0  # only gate pushes

    gate = subprocess.run([sys.executable, str(SCRIPTS_DIR / "coverage_gate.py")])
    if gate.returncode != 0:
        print(
            "⛔ Push blocked by coverage gate: test coverage is below 80%. "
            "Add tests until coverage passes, then push again.",
            file=sys.stderr,
        )
        return 2  # exit code 2 => Claude Code blocks the tool call

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
