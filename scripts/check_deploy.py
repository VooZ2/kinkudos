#!/usr/bin/env python3
"""Run Django deployment checks and reject unexpected warnings."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# These are deliberate self-hosting choices: subdomains are not automatically
# assumed to be HTTPS, and preload enrollment is an operator decision.
EXPECTED_WARNING_IDS = frozenset({"security.W005", "security.W021"})


def main():
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    print(output, end="")
    if result.returncode:
        return result.returncode

    warning_ids = set(re.findall(r"^\S+:\s+\(([^)]+)\)", output, re.MULTILINE))
    unexpected = sorted(warning_ids - EXPECTED_WARNING_IDS)
    if unexpected:
        print(
            "Unexpected Django deployment check warning(s): "
            + ", ".join(unexpected),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
