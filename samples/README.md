# 샘플 보고서

스킬 ID는 `gorani-` prefix를 쓰지만, 샘플 디렉터리는 산출물 종류를 따라 짧은 이름을 유지합니다.

스킬이 만드는 엑셀·JSON 결과의 예시입니다. 입력 JSON을 함께 두어 같은 결과를 다시 만들 수 있습니다.

## gorani-cve-scan

| 파일 | 내용 |
| --- | --- |
| `vex-input.json` | 정규화된 스캔 결과 입력 |
| `cve-report-sample.xlsx` | VEX 엑셀 보고서 (요약, VEX 판정, 원본 findings, 실행 로그) |
| `cve-report-sample.vex.json` | OpenVEX JSON |

VEX 엑셀과 OpenVEX는 사용자가 요청했을 때만 생성되는 선택 산출물의 예시입니다. 요청하지 않으면 스캔 요약과 조치 목록만 만듭니다.

재생성:

```bash
python3 skills/gorani-cve-scan/scripts/vex_xlsx.py --input samples/cve-scan/vex-input.json --outdir samples/cve-scan --name cve-report-sample
```

## gorani-release-check

| 파일 | 내용 |
| --- | --- |
| `release-check-input.json` | 브랜치·리비전 diff 점검 항목 입력 (샘플은 branch-merge-base) |
| `release-check-sample.xlsx` | 릴리스 점검 엑셀 보고서 (P0~P4, 역할·점검 항목, 변경 파일, 커밋, 실행 로그) |

재생성:

```bash
python3 skills/gorani-release-check/scripts/release_xlsx.py --input samples/release-check/release-check-input.json --outdir samples/release-check --name release-check-sample
```

리비전 비교 컨텍스트는 `compare_revisions.py --mode revision --from <ref> --to <ref> --out .qa/release-check-input.json`로 만듭니다. 샘플 JSON은 브랜치 merge-base 모드입니다.

## gorani-report

| 파일 | 내용 |
| --- | --- |
| `issue-body-sample.md` | 스킬 개선 요청 이슈 본문 샘플 (환경·도구 버전·재현 절차) |
| `format-idea-sample.md` | Excel 양식 제안 이슈 본문 샘플 (제안·기대 효과·현재 양식) |

재생성:

```bash
python3 skills/gorani-report/scripts/report_issue.py \
  --skill gorani-table-spec \
  --kind enhancement \
  --summary "DB 모드에서 테이블 설명이 비어 있습니다" \
  --expected "COMMENT ON 설명이 명세서에 표시됩니다." \
  --actual "설명 열이 모두 비어 있습니다." \
  --steps "1. DB에 COMMENT를 추가합니다. 2. table_spec.py를 실행합니다." \
  --command "python3 skills/gorani-table-spec/scripts/table_spec.py --db-url \"$DATABASE_URL\" --outdir docs/db" \
  --error "warning: column comment lookup returned empty" \
  --tool "sqlglot=30.27.0" \
  --out samples/report/issue-body-sample.md \
  --no-duplicate-search
```

Excel 양식 제안:

```bash
python3 skills/gorani-report/scripts/report_issue.py \
  --skill gorani-table-spec \
  --kind format \
  --area excel \
  --summary "테이블 명세서 Excel의 설명 열과 시트 순서를 조정했으면 합니다" \
  --proposal "설명 열을 넓히고 요약 시트를 첫 번째로 고정합니다." \
  --benefit "긴 설명을 줄바꿈 없이 읽고 리뷰어가 요약을 먼저 봅니다." \
  --current "현재 설명 열이 좁고 요약 시트가 마지막에 있습니다." \
  --tool "openpyxl=3.1.5" \
  --out samples/report/format-idea-sample.md \
  --no-duplicate-search
```

이 명령은 드래프트만 만들고 GitHub 이슈를 생성하지 않습니다. 실제 생성은 사용자 확인 후 `--create`로 실행합니다.

## gorani-change-impact

| 파일 | 내용 |
| --- | --- |
| `artifact-manifest.example.json` | 산출물 옆에 두는 sidecar manifest 예시 |
| `pr-impact.yml` | 특정 경로가 바뀔 때만 stale 검사를 실행하는 GitHub Actions 예시 |
| `impact-sample.md` | full 모드 리포트 샘플 (변경 분류·갱신 필요·확인 제안) |
| `impact-sample.json` | 같은 내용의 기계 판독용 JSON |

이 샘플은 임시 git 저장소에서 만든 예시이며 commit hash는 설명용입니다. `pr-impact.yml`은 스킬 폴더를 저장소에 vendoring했거나 gorani 저장소를 체크아웃한 경우를 가정하므로, 실제 프로젝트에서는 `python3` 경로를 설치 위치에 맞춥니다. 실제 저장소에서는 아래처럼 실행합니다.

```bash
python3 skills/gorani-change-impact/scripts/change_impact.py --mode stale --working
python3 skills/gorani-change-impact/scripts/change_impact.py --mode full --base origin/main
```

`stale`은 갱신 대상이 없으면 아무 파일도 만들지 않습니다. `full`은 릴리스 전이나 요청 시에만 실행합니다. 리포트는 `.gorani/impact/`에 생기며 커밋하지 않습니다.

## gorani-api-contract-diff

| 파일 | 내용 |
| --- | --- |
| `old.yaml` | 이전 OpenAPI 3.x 스펙 |
| `new.yaml` | 새 OpenAPI 3.x 스펙 |
| `api-diff.md` | 결론(P0~P4)·먼저 확인할 것·API별 변경·공통 변경·before/after 예시 diff 리포트 |
| `api-diff.json` | 같은 findings·body_changes의 기계 판독용 JSON |
| `api-diff.artifact.json` | 갱신 판단용 sidecar manifest |

재생성:

```bash
python3 skills/gorani-api-contract-diff/scripts/api_diff.py --old samples/api-contract-diff/old.yaml --new samples/api-contract-diff/new.yaml --service "Share API" --release-version "1.1.0" --clients "web, ios, android" --out samples/api-contract-diff/api-diff.md --json-out samples/api-contract-diff/api-diff.json
```

## gorani-site-structure

| 파일 | 내용 |
| --- | --- |
| `site-structure-input.json` | 실제 프론트 레이아웃을 확인해 정리한 구조 인벤토리 |
| `site-structure-sample.xlsx` | 요약·사이트 구조·화면 목록·API 매핑·API only·표준 근거·검토 메모 |
| `site-structure-sample.md` | 같은 내용의 Markdown 구조도 |
| `site-structure-sample.html` | 검색·메뉴 트리·화면 표를 담은 자기완결 HTML |
| `site-structure-sample.artifact.json` | 갱신 판단용 sidecar manifest |

재생성:

```bash
python3 skills/gorani-site-structure/scripts/site_structure.py --input samples/site-structure/site-structure-input.json --outdir samples/site-structure --name site-structure-sample --formats xlsx,md,html
```

샘플은 가상의 Admin Console 레이아웃이며, 스크린샷 경로도 예시입니다. 실제 구조는 브라우저에서 메뉴·탭·역할별 노출을 확인해 입력 JSON을 채웁니다. Playwright 자동 수집은 선택 사항입니다.

## gorani-table-spec

| 파일 | 내용 |
| --- | --- |
| `schema.sql` | 테이블·컬럼·주석·관계·인덱스가 있는 샘플 PostgreSQL DDL |
| `table-spec.xlsx` | 요약·테이블 목록·컬럼 명세·관계·인덱스·파싱 메모 |
| `table-spec.md` | 같은 내용의 Markdown 명세서 |
| `table-spec.html` | 검색·목차·인쇄를 지원하는 자기완결 HTML 명세서 |
| `table-spec.artifact.json` | 갱신 판단용 sidecar manifest |

재생성:

```bash
python3 skills/gorani-table-spec/scripts/table_spec.py --ddl samples/table-spec/schema.sql --dialect postgres --project "Sample DB" --outdir samples/table-spec --name table-spec --formats xlsx,md,html
```

DB 모드:

```bash
python3 skills/gorani-table-spec/scripts/table_spec.py --db-url "$DATABASE_URL" --schema public --project "My Service" --outdir docs/db --name table-spec --formats xlsx,md,html
```

## gorani-license-notice

| 파일 | 내용 |
| --- | --- |
| `license-input.json` | SBOM 수집 결과 입력 |
| `third-party-notices.html` | 앱·백엔드에 게시하는 자기완결 고지 페이지 |
| `third-party-notices.md` | 같은 내용의 평문 |
| `third-party-notices-review.md` | 검토 필요 목록 (내부용, 배포 제외) |
| `third-party-notices-simple.html` | 이름·버전·GitHub 라이선스 링크만 담은 간소화 페이지 |
| `third-party-notices-simple.md` | 같은 내용의 markdown |

재생성:

```bash
python3 skills/gorani-license-notice/scripts/notice_build.py --input samples/license-notice/license-input.json --outdir samples/license-notice --name third-party-notices --formats html,md,review
python3 skills/gorani-license-notice/scripts/notice_build.py --input samples/license-notice/license-input.json --outdir samples/license-notice --name third-party-notices --simple
```

샘플 프로젝트와 `legacy-widget` 패키지는 가상입니다. 라이선스 원문은 실제 npm 패키지에서 가져왔고, unknown·전문 없음·copyleft 검토 항목을 함께 보여 줍니다. 간소화 샘플에서는 `legacy-widget`만 GitHub 저장소가 없어 링크가 `-`로 표시됩니다.

샘플은 `html,md,review` 기본 형식으로 생성합니다. 엑셀은 `--formats xlsx`를 추가했을 때만 만듭니다.

## gorani-release-note

| 파일 | 내용 |
| --- | --- |
| `release-input.json` | 큐레이션된 릴리스 노트 입력 |
| `release-notes.html` | 고객용 자기완결 릴리스 노트 페이지 |
| `release-notes.md` | 고객용 긴 버전 (GitHub Release·문서) |
| `release-notes-short.txt` | 스토어 짧은 버전 (기본 500자) |
| `release-notes-store.txt` | 스토어 긴 버전 (기본 4,000자) |
| `release-notes-internal.md` | commit 매핑·검토 기록 (내부용, 배포 제외) |

재생성:

```bash
python3 skills/gorani-release-note/scripts/notes_build.py --input samples/release-note/release-input.json --outdir samples/release-note --name release-notes --formats html,md,short,store,internal
```

샘플 제품·버전·링크는 가상입니다. 깨지는 변경, 알려진 문제, 고객 문의 경로, 내부 commit 매핑을 함께 보여 줍니다.

샘플은 전체 형식으로 생성합니다. 실제 프로젝트에서는 필요한 형식만 `--formats`로 지정합니다.

## gorani-spec-analysis

| 파일 | 내용 |
| --- | --- |
| `source/source.plain.md` | 단순 변환 원문 예시 (frontmatter 없음) |
| `source/source.md` | 추적용 변환 원문 예시 (frontmatter·페이지 표시) |
| `index.md` | 분석 범위·핵심 발견·결정 필요 항목 |
| `glossary.md` | 용어 사전과 동의어·충돌 |
| `domain.md` | 도메인 모델과 Mermaid 클래스 다이어그램 |
| `processes.md` | 예약·승인·수령·반납 프로세스 |
| `flows.md` | 예약·승인 Mermaid 플로우차트 |
| `validation.md` | finding 10건과 추적성 |

샘플 기획서는 가상이며 Markdown 입력이라 PDF·DOCX 변환 손실 검증은 포함하지 않습니다. 실제 변환은 스킬의 형식별 도구 표를 따릅니다.

ID는 `V/P/F-{AREA}-{TOPIC}-{NN}` 형식을 사용합니다. 샘플은 `P-RESERVATION-CREATE-01`, `F-RESERVATION-CREATE-01`, `V-PROC-RETURN-01`처럼 접두사에서 내용 영역을 유추할 수 있게 했고, `RESERVATION`은 샘플 `index.md`에서 추가한 프로젝트별 AREA입니다.

각 문서 상단에는 문서 지도가 있고, `index.md`에는 Finding/Process/Flow Index가 있습니다. 프로세스·플로우·finding은 서로 상대 링크와 앵커로 연결됩니다. 샘플은 원문 보존 `both`, ID·링크 수준 `full`을 사용합니다.

## 주의

- 샘플 데이터는 형식을 보여주기 위한 가상 데이터입니다. 실제 프로젝트 결과가 아닙니다.
- gorani-cve-scan·gorani-release-check 샘플과 gorani-license-notice의 `--xlsx`는 `openpyxl`이 필요합니다: `python3 -m pip install --user openpyxl`
- gorani-table-spec은 DDL 모드에 `sqlglot`, DB 모드에 `sqlalchemy`와 DB 드라이버, xlsx 생성 시 `openpyxl`이 필요합니다: `python3 -m pip install --user sqlglot sqlalchemy openpyxl`
- gorani-site-structure는 xlsx 생성 시 `openpyxl`이 필요합니다. Playwright 자동 수집을 선택한 경우에만 Playwright와 브라우저 바이너리가 필요합니다.
- gorani-change-impact는 Python 3와 git만 필요합니다. 추가 패키지는 설치하지 않습니다.
- gorani-report는 Python 3와 `gh`가 필요합니다. 실제 이슈 생성에는 `gh auth login` 인증이 필요합니다.
- PostgreSQL DB 모드는 `psycopg[binary]`, MySQL은 `pymysql`, SQL Server는 `pymssql`, Oracle은 `oracledb`를 추가로 설치합니다.
- gorani-release-note는 표준 라이브러리만 사용합니다.
- 스크립트나 시트 구성을 바꾸면 샘플도 다시 생성해 같은 변경에 포함합니다.
