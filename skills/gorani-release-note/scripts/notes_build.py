#!/usr/bin/env python3
"""고객용 릴리스 노트를 만든다.

입력: 큐레이션된 릴리스 노트 JSON (SKILL.md 의 입력 형식 참고)
출력: release-notes.md, release-notes.html, release-notes-short.txt,
      release-notes-store.txt, release-notes-internal.md
      --model-out 을 주면 렌더링 전 리포트 모델 JSON도 저장한다.

구현은 notes_build 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from notes_build.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
