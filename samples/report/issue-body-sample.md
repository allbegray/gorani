## 요약

DB 모드에서 테이블 설명이 비어 있습니다

## 종류

개선 (`enhancement`)

## 제안

COMMENT ON 설명이 명세서에 표시됩니다.

## 현재 동작·양식

설명 열이 모두 비어 있습니다.

## 참고한 화면·명령

1. DB에 COMMENT를 추가합니다. 2. table_spec.py를 실행합니다.

## 실행 명령

```bash
python3 skills/gorani-table-spec/scripts/table_spec.py --db-url "$DATABASE_URL" --outdir docs/db
```

## 환경

| 항목 | 값 |
| --- | --- |
| 스킬 | gorani-table-spec |
| 스킬 버전 | 3.21.0 |
| 스킬 갱신일 | 2026-11-05 |
| skill source commit | 6f6f9a6+dirty |
| OS | macOS-27.2-arm64-arm-64bit-Mach-O |
| Python | 3.14.7 |
| Shell | zsh |
| 도구 | sqlglot=30.27.0 |

## 참고 로그

```text
warning: column comment lookup returned empty
```

## 공개 안전 확인

- [x] 고객 정보·시크릿·내부 URL을 포함하지 않았습니다.
- [x] 제안에 필요한 최소 정보만 포함했습니다.
- [x] 이 이슈가 공개 저장소에 게시된다는 점을 확인했습니다.

---

이 이슈는 `gorani-table-spec` 사용 중 `gorani-report`로 작성했습니다.
