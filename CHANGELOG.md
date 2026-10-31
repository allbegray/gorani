# 변경 이력

최신 버전은 3.15.0(2026-10-31)입니다. 3.15.0 이전 이력은 git log와 태그로 확인합니다.

## 3.15.0 · 2026-10-31

`gorani-ask` 스킬 라우터 추가

**추가**

- 사용자의 결과물·가진 자료·작업 단계를 보고 첫 스킬과 이어질 순서를 추천
- 릴리스, API 변경, DB 변경, 기획서 분석, 의존성·보안, 문서 정리 작업 경로 제공
- 추천 스킬의 이유·준비물·다음 단계 출력
- 스킬을 대신 실행하지 않고 사용자가 진행을 원할 때 해당 스킬로 넘김
- 스킬 추가·이름 변경·삭제 시 `gorani-ask` 지도 갱신 규칙 추가

**변경**

- README 스킬 표·설치·프롬프트 목록에 `gorani-ask` 등록
- AGENTS 2장 변경 계약과 3장 스킬 계약에 `gorani-ask` 추가

## 3.14.0 · 2026-10-31

`gorani-site-structure` 추가

**추가**

- 실제 프론트 레이아웃에서 확인한 메뉴·탭·화면 구조를 `site-structure-input.json`으로 정리
- `site-structure.xlsx`: 요약, 사이트 구조, 화면 목록, API 매핑, API only, 표준 근거, 검토 메모
- `site-structure.md`, 자기완결 `site-structure.html` 생성
- KRDS 디지털 정부서비스 UI/UX 가이드라인과 전자정부 웹사이트 품질관리 지침을 표준 근거로 기록
- 메뉴 depth 최소 2·최대 3, 3Depth 초과는 상세·탭·액션으로 분리
- API only를 구조도와 분리하고 스크린샷은 `screens/` 파일 경로로 기록
- Playwright 자동 수집은 선택 사항으로 두고 에이전트의 실제 화면 확인을 기본으로 함
- `samples/site-structure/` 입력 JSON과 Excel·Markdown·HTML 샘플

**변경**

- README 스킬 표·설치·예시·샘플 목록에 `gorani-site-structure` 등록
- AGENTS 3장에 `gorani-site-structure` 계약 추가

## 3.13.0 · 2026-10-31

`gorani-table-spec` HTML 산출물 추가

**추가**

- `--formats html`: 검색·목차·인쇄를 지원하는 자기완결 `table-spec.html` 생성
- Excel·Markdown·HTML 중 사용자가 고른 형식만 생성
- HTML은 외부 CSS·JS·폰트·이미지 없이 CSP로 외부 요청 차단
- 샘플 `samples/table-spec/table-spec.html` 추가

**변경**

- `--formats` 기본값을 `xlsx,md,html`로 조정
- `md`·`html`만 선택하면 openpyxl 없이 동작
- README·AGENTS·samples/README에 형식 선택과 HTML 설명 추가

## 3.12.0 · 2026-10-31

`gorani-table-spec` 추가

**추가**

- SQL DDL 또는 실제 DB에서 테이블·컬럼·PK/FK·UNIQUE·NOT NULL·DEFAULT·설명·인덱스를 추출
- `table-spec.xlsx`: 요약, 테이블 목록, 컬럼 명세, 관계, 인덱스, 파싱 메모
- `table-spec.md`: 같은 내용의 Markdown 명세서
- DDL: `CREATE TABLE`, `ALTER TABLE`, `COMMENT ON`, `CREATE INDEX`, `DROP TABLE` 지원
- DB: SQLAlchemy Inspector로 테이블·컬럼·PK·FK·UNIQUE·인덱스·COMMENT 조회, `--schema` 지원
- SQL Server 시스템 테이블 기본 제외, `--include-system` 옵션, MySQL UTF-8 연결 예시
- `--dialect auto`와 PostgreSQL·MySQL·SQLite·MSSQL·Oracle 지정
- `--formats md`만 선택하면 openpyxl 없이 동작, `--strict`는 경고 시 exit 1
- DB URL 비밀번호 마스킹, 읽기 전용 계정 권장
- `samples/table-spec/` DDL과 샘플 명세서

**변경**

- README 스킬 표·설치·예시·샘플 목록에 `gorani-table-spec` 등록
- AGENTS 3장에 `gorani-table-spec` 계약 추가

## 3.11.0 · 2026-10-30

`gorani-license-notice` 간소화 페이지 옵션 추가

**추가**

- `--simple`/`--minimal`: 의존성 이름·버전·GitHub 라이선스 링크만 담은 `third-party-notices-simple.html`·`.md` 생성
- GitHub 저장소 URL 정규화와 `blob/HEAD/<license file>` 링크 생성. `license_source` 파일명을 사용하고 없으면 `LICENSE`
- GitHub 링크가 없는 패키지는 `-`로 표시하고 `missing_github_links`로 집계
- `collect_licenses.py`가 SBOM에 저장소가 없을 때 설치된 `package.json`의 `repository`를 보조로 사용
- `samples/license-notice/` 간소화 HTML·md 샘플

**변경**

- README·AGENTS·samples/README에 간소화 옵션과 전체 고지 의무 대체 불가 주의 추가

## 3.10.0 · 2026-10-30

`gorani-release-check` 우선순위 P0~P4 조정

**변경**

- Google Issue Tracker P0~P4 기준 적용. P0 전면 중단, P1 핵심 기능 장애, P2 배포 전 확인, P3 여유 시 확인, P4 참고
- 기존 P0/P1/P2 3단계를 P0~P4 5단계로 확장. P0는 전면 중단 근거가 있을 때만 사용
- 엑셀 요약에 P0~P4 집계와 기준을 표시하고, 우선순위 드롭다운·색상·ID 규칙 확장
- 샘플 JSON 우선순위와 `release-check-sample.xlsx` 재생성
- README·AGENTS·samples/README의 P0/P1/P2 설명 갱신

## 3.9.0 · 2026-10-29

API 계약 변경 점검 스킬 추가

**추가**

- `gorani-api-contract-diff`: OpenAPI 3.x 이전·새 스펙 비교
- `api_diff.py`: 경로·오퍼레이션·파라미터·스키마·enum·인증 변경 수집
- breaking/risky/non-breaking/info 분류와 클라이언트 영향·배포 전·테스트 체크리스트
- 요청·응답 body 스키마 변경과 before/after JSON diff (`body_changes`)
- 읽기 쉬운 리포트: P0~P4 건수 결론 → 먼저 확인할 것 → API별 변경 → 공통 변경 → 체크리스트
- Google Issue Tracker P0~P4 기준을 참고해 breaking을 P0/P1/P2, risky를 P3, non-breaking·info를 P4로 구분. breaking이 항상 P0는 아님
- API별 변경에 `P0`(전면 중단)·`P1`(배포 전 수정)·`P2`(배포 전 확인)·`P3`(호환성 확인)·`P4`(참고) 표시, 같은 변경이 여러 API에 걸치면 영향 API를 함께 표시
- body 예시를 이전/이후 JSON diff(`-`/`+`)로 표시
- `GET /shares → 응답 200 본문 → ownerEmail` 위치 표기와 부록 전체 변경 목록
- `--fail-on-breaking` CI 차단 옵션
- `samples/api-contract-diff/` old/new 스펙과 리포트

**변경**

- README 스킬 표·설치·예시·샘플 목록에 `gorani-api-contract-diff` 등록
- AGENTS 3장에 `gorani-api-contract-diff` 계약 추가

## 3.8.0 · 2026-10-29

`gorani-release-check` 역할 컬럼·비개발자 문장

**추가**

- 점검 항목 표에 `역할` 컬럼 추가. `ADMIN` → `관리자`처럼 한국어로 표시
- `items.role` 코드: ADMIN, PM, QA, DEV, OPS, SEC, DATA, DESIGN, ETC, UNASSIGNED
- 점검 항목·기대 결과를 비개발자도 이해할 수 있는 사용자 관점 문장으로 작성하는 규칙
- 엑셀 점검 항목에서 `변경 근거` 열 제거. 기술 근거는 입력 JSON에만 보관

**변경**

- 샘플 점검 항목을 쉬운 문장으로 수정
- README·AGENTS·samples/README 갱신, 샘플 xlsx 재생성

## 3.7.0 · 2026-10-29

`gorani-release-check` 리비전 비교 추가

**추가**

- `compare_revisions.py`: 브랜치·리비전 diff 컨텍스트와 점검 JSON 골격 생성
- 비교 모드: `branch-merge-base`, `branch-tip`, `revision`, `revision-merge-base`
- `comparison_mode`, `base_commit`, `head_commit`, `old_path` 입력 필드
- 엑셀 요약에 비교 방식·비교 기준 표시

**변경**

- SKILL.md를 브랜치/리비전 모드로 확장
- README·AGENTS·samples/README 갱신
- 샘플 JSON에 `comparison_mode` 추가, 샘플 xlsx 재생성

## 3.6.0 · 2026-10-28

MIT 라이선스 추가

**추가**

- `LICENSE` (MIT, Copyright (c) 2026 allbegray)

**변경**

- README에 라이선스 섹션 추가

## 3.5.0 · 2026-10-28

IntelliJ에서 문서 간 링크가 동작하도록 앵커 방식 변경

**변경**

- 프로세스·플로우·finding 제목을 ID만으로 쓰고, 이름은 다음 줄로 이동
- HTML `<a id>` 앵커를 제거하고 Markdown 제목을 앵커로 사용
- `validation.md`를 finding별 `#### V-...` 섹션과 2열 표로 재구성
- `check_links.py`가 제목 앵커를 기준으로 링크 검사

## 3.4.0 · 2026-10-28

소스 파일 디렉터리 분리

**변경**

- `source/source.plain.md`와 `source/source.md`를 `source/` 디렉터리로 이동
- `index.md` 문서 지도와 산출물 목록의 소스 경로 갱신
- `check_links.py`가 하위 디렉터리의 markdown 링크·앵커를 재귀 검사

## 3.3.0 · 2026-10-28

모든 스킬 공통 도구 자동 설치 원칙

**추가**

- 모든 `SKILL.md`에 `## 도구 설치` 절 추가
- AGENTS 5장과 README에 공통 설치 원칙 추가
- OS·언어 패키지 관리자 우선, 필요한 도구만 설치, `sudo -n`만 사용, 설치 후 `command -v`·`--version` 확인
- 공식 패키지·저장소만 사용하고 `curl | sh`·출처 불명 바이너리·임의 URL 설치 금지
- 설치 도구·버전·실패 사유를 결과나 evidence에 기록

**변경**

- 기존의 “도구를 임의로 설치하지 않음” 문구를 자동 설치 정책으로 교체
- 설치 거부·실패 시 대체 도구나 입력 파일을 요청하도록 실패 처리 보강

## 3.2.0 · 2026-10-28

단순 변환 원문 추가

**추가**

- `source.plain.md`: 메타데이터·표 번호·레이아웃 주석 없는 단순 markdown 변환
- `source.md`는 추적용 메타데이터·페이지 표시·warnings를 유지
- 변환 원문 보존 여부를 `both`/`plain`/`trace`/`none`으로 선택
- ID·링크 작업 수준을 `full`/`ids`/`none`으로 선택

**변경**

- `index.md` 문서 지도와 산출물 목록에 `source.plain.md` 추가
- README·AGENTS·samples/README에 단순 변환 원문 설명 추가

## 3.1.0 · 2026-10-28

기획서 분석 스킬 추가

**추가**

- `gorani-spec-analysis`: 기획서를 markdown으로 변환하고 용어·도메인·프로세스·Mermaid 플로우차트·검증 리포트 생성
- `source`, `index`, `glossary`, `domain`, `processes`, `flows`, `validation` 7종 산출물
- PDF·DOCX·PPTX·HWP·XLSX·Markdown 변환 도구 선택과 충실도 점검 절차
- 사실·추론·질문 분리, blocker/major/minor/question 검증과 추적성
- `V/P/F-{AREA}-{TOPIC}-{NN}` 의미 기반 ID 규칙과 `index.md`의 AREA 카탈로그·ID Index
- 문서 지도, Finding/Process/Flow Index, 문서 간 상대 링크·앵커와 링크 검사 절차
- `scripts/check_links.py`: 상대 링크·앵커 검사 스크립트

**변경**

- README 스킬 표·설치·예시에 `gorani-spec-analysis` 등록
- AGENTS 3장에 `gorani-spec-analysis` 계약 추가
- `samples/spec-analysis/` 샘플 패키지 추가
- 샘플과 문서의 ID를 의미 기반 접두사로 변경

## 3.0.0 · 2026-10-28

스킬 ID에 `gorani-` prefix 적용

**변경**

- 모든 스킬 폴더와 frontmatter `name`을 `gorani-` prefix로 변경
- `docs-governance` → `gorani-docs-governance`
- `cve-scan` → `gorani-cve-scan`
- `release-check` → `gorani-release-check`
- `license-notice` → `gorani-license-notice`
- `release-note` → `gorani-release-note`
- `dependency-update` → `gorani-dependency-update`
- README 설치 for 루프, 프롬프트 `S` 값, raw URL 경로, AGENTS 계약, samples 재생성 경로 갱신

**마이그레이션**

- 기존 심볼릭 링크(`~/.claude/skills/cve-scan`, `.opencode/skills/cve-scan` 등)를 삭제하고 새 ID로 다시 설치
- 기존 raw URL(`skills/cve-scan/SKILL.md`)은 새 경로(`skills/gorani-cve-scan/SKILL.md`)로 교체
- OpenCode는 `@gorani-cve-scan`, Claude Code는 `/gorani-cve-scan`으로 호출. `/gorani:cve-scan`은 플러그인 네임스페이스가 필요

## 2.3.0 · 2026-10-28

보고서·산출물 선택화

**변경**

- `cve-scan`: VEX 엑셀·OpenVEX 보고서를 사용자 요청 시에만 생성
- 요청하지 않으면 CVE 요약·조치 목록만 보고하고 openpyxl 없이 동작
- `license-notice`: `--formats html,md,review,xlsx`로 산출물 선택. 기본 html,md,review
- `release-note`: `--formats html,md,short,store,internal`로 산출물 선택. 기본 전체
- 선택한 형식만 생성·갱신하고, 선택하지 않은 기존 파일은 건드리지 않음
- README·AGENTS에 선택 동작과 openpyxl 조건 반영

## 2.2.0 · 2026-10-28

의존성 업데이트 모드 스킬 추가

**추가**

- `dependency-update`: 언어·프레임워크 최신 안정화(기본), CVE 최소 수정, 전체 최신 안정의 3모드
- 모드별 장단점: 1 호환성·패스트 팔로워, 2 CVE 보완·관리 복잡도, 3 최신화·호환성 테스트 필수
- 생태계별 네이티브 확인·적용·검증 절차와 프레임워크 관리 판정 근거 표
- npm/pnpm/yarn, pip/Poetry/uv, Flutter, Maven/Gradle, .NET, Go, Cargo, Bundler, Composer 절차

**변경**

- README 스킬 표·설치·예시에 `dependency-update` 등록
- AGENTS 3장에 `dependency-update` 계약 추가

## 2.1.0 · 2026-10-27

오픈소스 고지 페이지·고객용 릴리스 노트 추가

**추가**

- `license-notice`: SBOM과 패키지의 LICENSE·NOTICE에서 라이선스 전문·저작권 수집
- 자기완결 HTML 고지 페이지: 검색, 라이선스별 접기, 라이트·다크 모드, 외부 요청 없음
- `--xlsx` 검토용 엑셀, `--fail-on-review` CI 게이트, `--exclude-dev`
- `samples/license-notice/`: 입력 JSON, HTML, md, 검토 목록
- `release-note`: git 범위의 변경을 고객 관점으로 재작성
- `collect_changes.py`: conventional commit·키워드 분류, 내부 변경 제외 제안, commit 매핑
- `notes_build.py`: 자기완결 HTML, md, 스토어 짧은·긴 요약, 내부 검토 기록
- `--strict` 검증과 입력 `limits` 기반 앱스토어 글자 수 확인
- `samples/release-note/`: 입력 JSON과 고객용·내부용 결과

**변경**

- README 스킬 표·설치·예시에 `license-notice`, `release-note` 등록
- AGENTS 3장에 두 스킬의 계약 추가

## 2.0.0 · 2026-10-27

스킬 모음집으로 전환

**추가**

- `docs-governance`: GitHub 기본 문서 11종 생성·유지 (루트 6종, `.github` 5종)
- `cve-scan`: osv-scanner·trivy·syft·grype 교차 점검, VEX 엑셀과 OpenVEX JSON 생성
- `release-check`: main·develop diff 기반 P0/P1/P2 점검 엑셀, 개발자 전용 항목 하단 배치
- `samples/`: 두 스킬의 입력 JSON과 xlsx·vex.json 결과, 재생성 명령

**변경**

- 저장소 성격: 프롬프트 모음집 → 실무 프로젝트용 스킬 모음집
- 스킬 형식: `skills/<이름>/SKILL.md` + `name`/`description` frontmatter
- docs-governance: 기존 6종 문서 기준에서 GitHub 기본 문서 세트 기준으로 재작성
- README·AGENTS·CHANGELOG를 새 양식으로 재작성

**제거**

- `prompts/` 디렉터리 (`skills/<이름>/SKILL.md`로 대체)
- 기존 6종(AGENTS/BACKLOG/SOLUTION) 문서 기준과 graphify 규칙

## 버전 규칙

`MAJOR.MINOR.PATCH`를 씁니다. 호환되지 않는 변경은 MAJOR, 기능 추가는 MINOR, 수정은 PATCH입니다.
