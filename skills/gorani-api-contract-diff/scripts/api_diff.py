#!/usr/bin/env python3
"""Compare two OpenAPI 3.x specs and write a contract-change report.

Usage:
    python3 api_diff.py --old old.yaml --new new.yaml --out api-diff.md
    python3 api_diff.py --old old.json --new new.json --json-out api-diff.json
    python3 api_diff.py --old old.yaml --new new.yaml --fail-on-breaking

The report is a spec-level comparison. Runtime behavior, gateway policy, and
client implementation still need confirmation.

구현은 api_diff 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from api_diff.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
