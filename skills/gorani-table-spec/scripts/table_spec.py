#!/usr/bin/env python3
"""SQL DDL 또는 실제 DB에서 테이블 명세서(Markdown·Excel·HTML)를 만든다.

입력: SQL DDL 파일 또는 SQLAlchemy DB URL
출력: table-spec.md, table-spec.xlsx, table-spec.html, table-spec.artifact.json
      --model-out 을 주면 렌더링 전 리포트 모델 JSON도 저장한다.

DDL은 sqlglot으로, DB는 SQLAlchemy Inspector로 읽는다. 실제 DB 모드는
접속 시점의 스키마를 읽으며 스키마·데이터를 수정하지 않는다.

구현은 table_spec 패키지에 있다. 이 파일은 기존 CLI 진입점만 유지한다.
"""

from table_spec.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
