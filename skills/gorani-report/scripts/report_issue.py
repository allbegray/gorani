#!/usr/bin/env python3
"""gorani 스킬 오류·개선점을 GitHub 이슈로 정리한다.

기본은 드래프트 생성이다. `--create` 또는 `--comment-on`을 줘야 실제로
GitHub에 쓴다. 본문은 만들기 전에 홈 경로·토큰·비밀번호·이메일·내부 URL을
마스킹하고, 남은 위험 패턴이 있으면 `--force` 없이는 생성하지 않는다.

구현은 report_issue 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from report_issue.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
