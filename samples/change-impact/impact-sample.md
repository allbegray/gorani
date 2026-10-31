# 변경 영향 — 전체 요약

- 모드: full
- 기준: 147977562bb7e4de184fe5af9d1d3c390507c8e2
- HEAD: 87b272f1c7f839f37971ea139b6ebeb3d92eeb3d
- 기준 시각: 2026-10-31T15:00:00+09:00
- 변경 파일: 5
- 갱신 필요: 3
- 변경 없음: 0
- 확인 불가: 0
- 변경 분류: frontend 1, api 1, db 1, config 1, dependencies 1

## 갱신 필요

| 산출물 | 스킬 | 매칭된 변경 | 재생성 |
| --- | --- | --- | --- |
| `docs/api/share-api/api-diff.md` | `gorani-api-contract-diff` | openapi/share.yaml | `python3 skills/gorani-api-contract-diff/scripts/api_diff.py --old openapi/share-v1.yaml --new openapi/share.yaml --out docs/api/share-api/api-diff.md` |
| `docs/db/table-spec.xlsx` | `gorani-table-spec` | db/migrations/002_status.sql | `python3 skills/gorani-table-spec/scripts/table_spec.py --ddl db/migrations --dialect postgres --outdir docs/db --name table-spec` |
| `docs/site-structure/site-structure.xlsx` | `gorani-site-structure` | src/app/users/page.tsx | `python3 skills/gorani-site-structure/scripts/site_structure.py --input docs/site-structure/site-structure-input.json --outdir docs/site-structure --name site-structure` |

## 변경 분류

- frontend: 1건
  - `src/app/users/page.tsx`
- api: 1건
  - `openapi/share.yaml`
- db: 1건
  - `db/migrations/002_status.sql`
- config: 1건
  - `.env.example`
- dependencies: 1건
  - `package.json`

## 확인 제안

- `gorani-site-structure` — 화면·메뉴·레이아웃 영향 여부를 실제 프론트에서 확인하고 구조도를 갱신합니다.
- `gorani-api-contract-diff` — 이전·새 OpenAPI 스펙을 비교해 breaking change와 클라이언트 영향을 확인합니다.
- `gorani-table-spec` — 테이블 명세를 갱신하고 마이그레이션 잠금·데이터 손실 위험을 확인합니다.
- `수동 확인` — .env.example·compose·Kubernetes manifest의 환경변수가 서로 일치하는지 확인합니다.
- `gorani-cve-scan` — 의존성 CVE와 라이선스 고지 갱신 필요 여부를 확인합니다. 이어서 gorani-dependency-update를 검토합니다.

## 릴리스 절차

- 이 리포트를 확인한 뒤 `gorani-release-check` → `gorani-release-note` 순서로 진행합니다.

> 이 리포트는 산출물을 수정하지 않습니다. 표시된 갱신 명령을 확인한 뒤 사용자가 직접 실행합니다.
