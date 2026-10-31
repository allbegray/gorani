## 요약

DB 모드에서 테이블 설명이 비어 있습니다

## 종류

개선 (`enhancement`)

## 제안

COMMENT ON으로 작성한 테이블·컬럼 설명이 명세서에 표시됩니다.

## 기대 효과

PostgreSQL 16, SQLAlchemy 2.1.6. DDL 모드에서는 설명이 정상입니다.

## 현재 동작·양식

설명 열이 모두 비어 있고, 원본 DB에는 COMMENT가 있습니다.

## 참고한 화면·명령

1. PostgreSQL에서 COMMENT ON TABLE users IS ... 로 설명을 추가합니다.
2. table_spec.py --db-url "$DATABASE_URL" --outdir docs/db --formats xlsx,md 로 실행합니다.
3. table-spec.md의 설명 열을 확인합니다.

## 실행 명령

```bash
python3 skills/gorani-table-spec/scripts/table_spec.py --db-url "$DATABASE_URL" --outdir docs/db --formats xlsx,md
```

## 환경

| 항목 | 값 |
| --- | --- |
| 스킬 | gorani-table-spec |
| 스킬 버전 | 3.17.0 |
| 스킬 갱신일 | 2026-10-31 |
| skill source commit | 136443a+dirty |
| OS | macOS-27.0.1-arm64-arm-64bit-Mach-O |
| Python | 3.15.2 |
| Shell | zsh |
| 도구 | sqlglot=30.27.0 SQLAlchemy=2.1.6 |

## 참고 로그

```text
warning: column comment lookup returned empty for schema public
```

## 공개 안전 확인

- [x] 고객 정보·시크릿·내부 URL을 포함하지 않았습니다.
- [x] 제안에 필요한 최소 정보만 포함했습니다.
- [x] 이 이슈가 공개 저장소에 게시된다는 점을 확인했습니다.

---

이 이슈는 `gorani-table-spec` 사용 중 `gorani-report`로 작성했습니다.
