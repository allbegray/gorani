#!/usr/bin/env python3
"""프론트 레이아웃 인벤토리에서 사이트 구조도 산출물을 만든다.

입력: 실제 화면을 확인해 정리한 정규화 JSON
출력: site-structure.xlsx, site-structure.md, site-structure.html
      --model-out 을 주면 렌더링 전 리포트 모델 JSON도 저장한다.

API 목록은 화면 구조의 근거가 아니다. 페이지 계층은 menu_path와 parent_id로
표현하고, API는 화면별 매핑과 API only 부록으로만 기록한다.

구현은 site_structure 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from site_structure.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
