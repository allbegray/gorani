#!/usr/bin/env python3
"""오픈소스 고지 페이지를 만든다.

입력: 정규화된 라이선스 JSON (SKILL.md 의 입력 형식 참고)
출력: third-party-notices.html, third-party-notices.md,
      검토 항목이 있으면 third-party-notices-review.md,
      --xlsx 를 주면 third-party-notices.xlsx,
      --simple 이면 third-party-notices-simple.html, third-party-notices-simple.md
      --model-out 을 주면 렌더링 전 리포트 모델 JSON도 저장한다.

구현은 notice_build 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from notice_build.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
