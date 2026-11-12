#!/usr/bin/env python3
"""DB dump SQL을 사람이 작성한 스타일의 DDL로 바꾼다.

입력: pg_dump·mysqldump 등이 만든 SQL 파일
출력: schema.sql (정리된 DDL), 선택 시 schema.review.md (검토 메모)

구현은 ddl_format 패키지에 있다. 이 파일은 CLI 진입점만 유지한다.
"""

from ddl_format.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
