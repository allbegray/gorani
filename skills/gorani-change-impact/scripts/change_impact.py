#!/usr/bin/env python3
"""기존 산출물의 stale 여부를 값싸게 확인한다.

기본 모드(stale)는 `*.artifact.json` sidecar manifest와 git diff만 사용한다.
코드를 파싱하지 않고, 갱신 대상이 없으면 파일도 출력도 만들지 않는다.

`--mode full`은 릴리스 전이나 사용자가 요청할 때만 쓰는 영향도 요약이다.
산출물을 직접 수정하지 않고 갱신 명령과 확인 범위만 제안한다.

구현은 change_impact 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from change_impact.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
