# gorani-table-spec scripts

테이블 명세서 생성은 `입력 → 리포트 모델 → 렌더러` 순서로 나뉩니다.

```text
table_spec.py               기존 CLI 진입점 (얇은 래퍼)
table_spec/
  cli.py                    argparse, 출력 경로, 모델 저장, 렌더러 호출
  ddl.py                    SQL DDL 수집·파싱 (sqlglot)
  db.py                     SQLAlchemy Inspector 조회 (SQLAlchemy)
  model.py                  테이블 구조 병합·마무리와 리포트 모델 생성 (순수 Python)
  render_md.py              Markdown 렌더러
  render_html.py            자기완결 HTML 렌더러
  render_xlsx.py            XLSX 렌더러 (openpyxl)
  manifest.py               sidecar .artifact.json 생성
  constants.py              방언·출력 형식·시스템 스키마 상수
```

## 데이터 흐름

1. `ddl.py` 또는 `db.py`가 입력을 읽어 테이블 구조를 만듭니다.
2. `model.py`가 PK·FK·UNIQUE·인덱스·비고를 마무리하고 `schema_version`, `meta`, `summary`, `tables`, `warnings`, `sources`를 가진 리포트 모델을 만듭니다.
3. `render_md.py`, `render_html.py`, `render_xlsx.py`가 같은 모델을 각 형식으로 렌더링합니다.
4. `manifest.py`가 산출물·소스·재생성 명령을 기록합니다.
5. `cli.py`가 전체 순서와 파일 이름을 결정합니다.

## 리포트 모델

`--model-out PATH`로 렌더링 전 모델을 저장합니다.

| 필드 | 내용 |
| --- | --- |
| `schema_version` | 모델 스키마 버전 |
| `meta` | 프로젝트, 생성 시각, 입력 종류(`ddl`/`database`), 원본 표시, 방언, 파일 목록, 생성기 |
| `summary` | 테이블·컬럼·FK·인덱스·경고 수 |
| `tables` | 스키마·테이블명 순으로 정렬한 테이블 구조 |
| `warnings` | 파싱 경고 |
| `sources` | manifest에 기록할 소스 글롭 |

`--generated-at`은 모델·manifest·모든 렌더러의 생성 시각을 같은 값으로 고정합니다.

## 커스터마이징 지점

- Markdown 구성 변경: `render_md.py`
- HTML 구성·검색·스타일 변경: `render_html.py`
- XLSX 시트·컬럼·스타일 변경: `render_xlsx.py`
- DDL 파싱 규칙 변경: `ddl.py`
- DB 조회 범위·시스템 테이블 제외 규칙 변경: `db.py`
- 모델 필드 추가·집계 변경: `model.py`
- 새 출력 형식 추가: `render_<format>.py` 추가 후 `cli.py`에서 호출
- manifest 필드·재생성 명령 변경: `manifest.py`

## 의존성 격리

- `model.py`는 sqlglot·SQLAlchemy·openpyxl을 import하지 않습니다.
- `ddl.py`는 sqlglot을 선택적으로 import합니다. 없으면 `--ddl` 실행 시 설치 안내와 함께 종료합니다.
- `db.py`는 SQLAlchemy를 `introspect_db()` 실행 시점에 import합니다.
- `render_xlsx.py`는 openpyxl을 `write_xlsx()` 안에서만 import합니다. 따라서 `--formats md,html`은 openpyxl 없이 동작합니다.
- `table_spec.py`는 패키지 `table_spec`을 import하는 얇은 래퍼입니다. 기존 명령 경로를 그대로 씁니다.

```bash
python3 skills/gorani-table-spec/scripts/table_spec.py \
  --ddl samples/table-spec/schema.sql \
  --dialect postgres \
  --project "Sample DB" \
  --outdir samples/table-spec \
  --name table-spec \
  --formats xlsx,md,html \
  --model-out /tmp/table-spec-model.json \
  --generated-at 2026-10-31T19:10:52+09:00
```
