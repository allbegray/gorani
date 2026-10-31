# Gorani

`Gorani`는 '관리(管理)'를 빠르게 타이핑하다 생긴 오타 '고나리'에서 온 이름입니다.

AI CLI에 붙여 쓰는 실무 스킬 모음입니다. 스킬은 Agent Skills 표준(`SKILL.md`)을 따르므로 opencode와 Claude Code가 같은 파일을 읽습니다. 설치 없이 프롬프트로 넘길 수도 있습니다.

## 스킬

| 스킬 | 이럴 때 | 결과 |
| --- | --- | --- |
| `gorani-ask` | 어떤 스킬을 써야 할지 모를 때, 작업 순서를 정할 때 | 상황별 스킬·작업 순서 추천 |
| `gorani-change-impact` | 기존 산출물이 소스 변경으로 낡았는지 확인할 때, 릴리스 전 갱신 대상을 볼 때 | 갱신 필요 산출물·매칭된 변경·재생성 명령 |
| `gorani-report` | 스킬 오류·개선점을 GitHub 이슈로 남기고 싶을 때 | 마스킹된 이슈 드래프트·생성 URL |
| `gorani-docs-governance` | 프로젝트 문서 체계를 처음 잡을 때, 코드 변경 후 문서를 맞출 때 | 루트 문서 6종 + `.github` 5종 |
| `gorani-cve-scan` | 의존성 취약점을 확인할 때, 릴리스 전 보안을 볼 때 | CVE 요약·조치 목록, 요청 시 VEX 엑셀·OpenVEX |
| `gorani-release-check` | 운영 배포 전 브랜치·리비전 차이를 볼 때 | P0~P4 점검 엑셀 |
| `gorani-api-contract-diff` | API 스펙 변경이 클라이언트를 깨뜨리는지 볼 때 | API별 변경 리포트, 배포 전·테스트 체크리스트 |
| `gorani-license-notice` | 앱에 오픈소스 고지 페이지를 넣어야 할 때, 배포 전 라이선스를 점검할 때 | 선택한 고지 HTML·md·검토 목록·엑셀, 간소화 링크 페이지 |
| `gorani-release-note` | 고객에게 나갈 릴리스 노트를 써야 할 때, 앱 업데이트 안내를 준비할 때 | 선택한 HTML·md·스토어 요약·내부 기록 |
| `gorani-dependency-update` | 현재 언어·프레임워크 라인의 최신 안정으로 정렬할 때, CVE만 고칠 때, 라인까지 올릴 때 | 모드별 업데이트 계획·적용·검증 |
| `gorani-spec-analysis` | 기획서를 정리·검토할 때, 용어·도메인·프로세스·흐름을 뽑을 때 | markdown 원문, 용어 사전, 도메인 모델, 프로세스·플로우, 검증 리포트 |
| `gorani-table-spec` | DB 테이블 정의서를 만들 때, DDL이나 실제 DB로 스키마를 문서화할 때 | 테이블·컬럼·PK/FK·인덱스 명세 Excel·Markdown·HTML |
| `gorani-site-structure` | 실제 프론트 메뉴·레이아웃을 사이트 구조도로 정리할 때 | 메뉴 구조·화면 목록·API only·표준 근거 Excel·Markdown·HTML |

## 각 스킬이 하는 일

### gorani-ask

스킬 이름을 외우지 않아도 되도록, 지금 상황에 맞는 첫 스킬과 이어질 순서를 골라 줍니다.

- 결과물·가진 자료·작업 단계를 보고 가장 가까운 스킬을 추천
- 릴리스, API 변경, DB 변경, 기획서 분석, 문서 정리 같은 작업 경로 제시
- 추천한 스킬의 준비물과 다음 단계를 함께 안내
- 스킬을 대신 실행하지 않고, 사용자가 진행을 원할 때 해당 스킬로 넘김
- 새 스킬이 추가되면 `gorani-ask`의 스킬 지도도 함께 갱신

### gorani-change-impact

기존 스킬이 만든 산출물 옆의 `*.artifact.json` sidecar manifest와 git diff를 비교해, 갱신이 필요한 산출물만 알려 줍니다.

- 기본은 값싼 `stale` 모드. 코드 파싱 없이 `git diff`와 글롭만 사용
- 갱신 대상이 없으면 리포트 파일도 PR 코멘트도 만들지 않음
- `full` 모드는 릴리스 전이나 요청 시에만 실행하고 화면·API·DB·설정·의존성·테스트 영향을 분류
- 산출물을 자동 수정하지 않고 manifest의 `regenerate` 명령만 제안
- `gorani-site-structure`, `gorani-table-spec`, `gorani-api-contract-diff`가 manifest를 자동 생성
- PR CI는 특정 경로가 바뀔 때만 path-filter로 실행
- 결과: `.gorani/impact/impact-<head>-stale.md`, `.json` 또는 `-full.md`, `.json`
- `.gorani/`는 로컬 임시 산출물이므로 커밋하지 않음

### gorani-report

스킬 사용 중 만난 오류·개선·아이디어·양식 제안을 공개 GitHub 이슈로 정리합니다.

- 실행 명령·오류 로그·제안 내용·환경과 대상 스킬의 `metadata.version`·`metadata.updated`를 모아 드래프트 생성
- 홈 경로·토큰·비밀번호·DB URL 자격증명·이메일·내부 URL 마스킹
- Excel·Markdown·HTML 양식 제안과 새 아이디어도 오류와 같은 흐름으로 작성
- `--kind idea`·`--kind format`·`--area excel`로 제안 종류와 영역을 구분
- 중복 이슈를 먼저 검색하고, 기존 이슈 코멘트 또는 새 이슈를 선택
- 기본은 드래프트이며, 사용자 확인 후에만 `--create`로 실제 생성
- `gh`가 없거나 인증되지 않았으면 드래프트만 남기고 `gh auth login` 안내
- `.github/ISSUE_TEMPLATE/skill-report.yml` 양식으로 직접 보고도 가능
- 결과: `.gorani/report/<skill>-<timestamp>.md`, `--json` 메타데이터, 생성된 이슈 URL

### gorani-docs-governance

프로젝트를 먼저 읽고 실제 빌드·테스트 명령을 반영해 문서 11종을 만듭니다.

- 루트: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG
- `.github`: PULL_REQUEST_TEMPLATE, ISSUE_TEMPLATE 3종, CODEOWNERS

기존 문서는 지우지 않고 빠진 섹션만 채웁니다. LICENSE, 신고 연락처, CODEOWNERS 핸들은 확인 없이 만들지 않고, 비대화형 실행이면 "확인 필요"로 남깁니다.

### gorani-cve-scan

`syft`로 SBOM을 만들고 `grype`로 대조한 뒤 `osv-scanner`와 `trivy`로 교차 확인합니다. 대상은 소스 의존성이고 컨테이너 이미지는 다루지 않습니다.

- 같은 취약점은 하나로 합치고 높은 심각도를 채택
- 수정 버전이 있으면 `affected`, 없으면 `under_investigation`이 기본
- 기본 결과: CVE 요약과 조치 목록
- VEX 엑셀·OpenVEX JSON은 사용자가 요청할 때만 생성. 요청하지 않으면 openpyxl 없이 동작
- 요청 시 결과: `docs/security/cve-report-YYYY-MM-DD.xlsx`와 같은 이름의 `.vex.json`
- 패키지를 올리지는 않고 조치 목록만 제시

### gorani-release-check

브랜치 diff 또는 두 리비전 사이의 diff에서 커밋과 변경 파일을 모아 점검 항목을 만듭니다.

- 브랜치: `main...develop` merge-base 기본, `--tip`으로 tip 대 tip 비교
- 리비전: `v1.0.0..v1.2.0` 직접 비교, `--merge-base`로 공통 조상 기준 비교
- `compare_revisions.py`가 커밋·파일·통계 JSON을 만들고, `release_xlsx.py`가 엑셀을 생성
- Google Issue Tracker P0~P4 기준: P0 전면 중단 / P1 핵심 기능 장애 / P2 배포 전 확인 / P3 여유 시 확인 / P4 참고
- 점검 항목에 역할(`ADMIN` → 관리자) 컬럼을 추가
- 점검 항목·기대 결과는 비개발자도 이해할 수 있는 사용자 관점 문장으로 작성
- 엑셀에는 기술적인 `변경 근거` 열을 넣지 않고, 근거는 입력 JSON에만 보관
- QA가 확인할 항목과 개발자만 확인할 항목을 나누고, 개발자 항목은 시트 하단에 배치
- 결과: `docs/qa/release-check-YYYY-MM-DD.xlsx`
- 코드는 건드리지 않음

### gorani-api-contract-diff

OpenAPI 3.x 스펙 두 개를 비교해 계약 변경을 정리합니다.

- 입력: 이전·새 OpenAPI 3.x JSON/YAML
- breaking / risky / non-breaking / info 분류
- 결론(P0~P4 건수) → 먼저 확인할 것 → API별 변경 → 공통 변경 → 체크리스트 순서
- Google Issue Tracker의 P0~P4 기준을 API 계약 변경에 맞게 적용. breaking이 항상 P0는 아님
- API별 변경은 `P0`(전면 중단)·`P1`(배포 전 수정)·`P2`(배포 전 확인)·`P3`(호환성 확인)·`P4`(참고)로 표시
- 같은 변경이 여러 API에 걸치면 먼저 확인할 것에 영향 API를 함께 표시
- 요청·응답 body의 필드·필수값·enum 변경과 before/after JSON diff
- 위치를 `GET /shares → 응답 200 본문 → ownerEmail`처럼 표시
- 배포 전·테스트 체크리스트와 전체 변경 부록
- 결과: `docs/api/<service>/api-diff.md`, 선택 시 `api-diff.json`
- `--fail-on-breaking`으로 CI에서 breaking 변경 차단
- 스펙 기준 비교이며 런타임 동작·클라이언트 구현은 별도 확인

### gorani-license-notice

SBOM과 패키지의 LICENSE·NOTICE를 모아 앱에 게시할 고지 페이지를 만듭니다. 기본 결과는 엑셀이 아니라 자기완결 HTML입니다.

- `syft`로 SBOM을 만들고, 설치된 패키지에서 라이선스 전문과 저작권 표시를 수집
- 같은 라이선스 전문은 한 번만 수록하고, 패키지별 저작권은 각 패키지에 표시
- 결과: `docs/licenses/third-party-notices.html`, `.md`, 검토가 필요하면 `-review.md`
- 산출물은 `--formats`로 선택: `html`, `md`, `review`, `xlsx`. 기본은 `html,md,review`
- copyleft·복수 라이선스·미확인·전문 없음은 검토 목록으로 분리하고, 앱 페이지에는 내부 사유를 넣지 않음
- `--xlsx` 또는 `--formats xlsx`를 주면 검토용 엑셀도 생성. 기본 경로는 openpyxl 없이 동작
- `--simple`은 의존성 이름·버전·GitHub 라이선스 링크만 담은 `third-party-notices-simple.html`·`.md`를 생성
- 간소화 페이지는 전체 고지 의무를 대체하지 않으므로 배포에는 전체 HTML을 사용

### gorani-release-note

이전 릴리스 이후 변경을 고객이 읽을 문장으로 바꿉니다. 커밋을 그대로 나열하지 않고, 고객에게 보이는 변화만 골라 이점과 사용 방법을 설명합니다.

- `git log` 범위를 수집해 기능·개선·수정·보안으로 분류하고 내부 변경은 제외 후보로 표시
- 깨지는 변경은 가장 위에 두고, 고객이 따라 할 수 있는 조치를 함께 작성
- 결과: `docs/releases/release-notes.html`, `.md`, 스토어 짧은·긴 요약, 내부 검토 기록
- 산출물은 `--formats`로 선택: `html`, `md`, `short`, `store`, `internal`. 기본은 전체
- `--strict`로 commit 매핑·지원 경로·링크를 검증
- 앱스토어 글자 수 제한은 입력의 `limits`로 조정

### gorani-dependency-update

의존성 업데이트 방식을 세 가지로 나눠 사용자와 먼저 정합니다. 생태계별 스크립트를 두지 않고, 저장소의 패키지 매니저와 프레임워크 도구를 그대로 사용합니다.

| 모드 | 장점 | 주의 |
| --- | --- | --- |
| 1. 언어·프레임워크 최신 안정화 (기본) | 현재 라인의 호환성을 지키고 변경 범위가 작음 | 일부 CVE가 남을 수 있음. 프레임워크 패치를 빠르게 따라가는 패스트 팔로워 운영 필요 |
| 2. 모드 1 + CVE 재정의 | 잔여 CVE까지 보완 | BOM property override·버전 불일치로 의존성 관리가 지저분해질 수 있음. override 제거 계획 필요 |
| 3. 전체 최신 안정 | 모든 직접 의존성을 최신으로 맞춤 | 호환성이 깨질 수 있음. 호환성 체크와 충분한 테스트 케이스 필수, major 변경은 분리 권장 |

- major 변경·프레임워크 범위 밖 재정의·모드 3은 계획을 보여 주고 확인 후 적용
- npm/pnpm/yarn, pip/Poetry/uv, Flutter, Maven/Gradle, .NET, Go, Cargo, Bundler, Composer 절차를 안내

### gorani-site-structure

실제 프론트 화면에서 확인한 메뉴·탭·레이아웃을 기준으로 사이트 구조도를 만듭니다.

- 입력: 실제 화면을 확인해 작성한 `site-structure-input.json`
- API 스펙만으로 구조를 만들지 않고, 화면별 API 연결과 API only를 분리
- KRDS 디지털 정부서비스 UI/UX 가이드라인과 전자정부 웹사이트 품질관리 지침을 기준으로 기록
- 메뉴 depth는 최소 2Depth, 최대 3Depth. 상세·탭·액션은 부모 화면과 노출 방식으로 표현
- 스크린샷은 엑셀에 넣지 않고 `screens/` 파일 경로만 기록
- Playwright 자동 수집은 선택 사항. 기본은 에이전트가 실제 화면을 확인
- 결과: `docs/site-structure/site-structure.xlsx`, `.md`, `.html`
- `--formats`로 필요한 형식만 선택. `md`·`html`은 openpyxl 없이 동작

### gorani-spec-analysis

기획서 원본을 markdown으로 변환하고, 용어·도메인·프로세스·플로우차트·검증 결과를 한 패키지로 정리합니다.

- 입력: PDF, DOCX, PPTX, HWP, XLSX, Markdown
- 변환 원문 보존 여부를 먼저 선택: `both`(기본), `plain`, `trace`, `none`
- ID·링크 작업 수준을 선택: `full`(기본), `ids`, `none`. `full`은 시간이 더 걸리지만 검색·추적이 좋아짐
- 원본은 보존하고 `source/source.plain.md`에 단순 변환, `source/source.md`에 변환 도구와 손실 경고를 기록
- 결과: `docs/spec/<slug>/`에 분석 문서 6종과 `source/source.plain.md`, `source/source.md`
- ID는 `V/P/F-{AREA}-{TOPIC}-{NN}` 형식으로, 접두사에서 내용 영역을 유추
- 문서 상단 지도, Finding/Process/Flow Index, 상대 링크·앵커로 문서 간 이동
- 프로세스·플로우·finding 제목을 ID로 써서 IntelliJ·GitHub에서 링크가 동작
- [scripts/check_links.py](skills/gorani-spec-analysis/scripts/check_links.py)로 상대 링크와 앵커 검사
- 원문에 없는 규칙은 사실로 쓰지 않고 `추론`·`질문`으로 분리
- 변환 도구가 없으면 설치를 임의로 하지 않고 대체 도구나 markdown 입력을 안내

### gorani-table-spec

SQL DDL 또는 실제 DB에서 테이블 정의를 읽어 테이블 명세서를 만듭니다.

- 입력: `.sql`·`.ddl` 파일 또는 디렉터리, SQLAlchemy DB URL
- DDL: PostgreSQL·MySQL·SQLite·MSSQL·Oracle 방언과 `ALTER TABLE`·`COMMENT`·`INDEX` 반영
- DB: PostgreSQL·MySQL·SQLite·MSSQL·Oracle을 SQLAlchemy로 조회. 읽기 전용 계정 권장, 시스템 테이블 기본 제외
- 테이블·컬럼·데이터 타입·길이·PK·FK·UNIQUE·NOT NULL·DEFAULT·설명·인덱스 정리
- 결과: `docs/db/table-spec.xlsx`, `table-spec.md`, `table-spec.html`
- `--formats`로 Excel·Markdown·HTML 중 필요한 형식만 선택
- HTML은 검색·목차·인쇄를 지원하는 자기완결 페이지
- `--db-url`과 `--schema`로 실제 DB 스키마를 조회하고, 비밀번호는 결과에서 마스킹
- `--formats md` 또는 `html`만 주면 openpyxl 없이 동작
- `--strict`로 파싱 경고가 있을 때 CI에서 차단
- DDL 모드는 파일 기준, DB 모드는 접속 시점 스키마 기준

## 설치

스킬 폴더를 에이전트가 읽는 위치에 연결합니다. 심볼릭 링크를 쓸 수 없는 환경(Windows 등)에서는 같은 경로에 폴더를 복사하세요.

```bash
git clone https://github.com/allbegray/gorani.git ~/gorani
```

opencode — 프로젝트에만 적용하려면 그대로, 모든 프로젝트에 적용하려면 주석 처리된 줄과 바꿔 실행합니다.

```bash
SCOPE=.opencode/skills          # 프로젝트에만
# SCOPE=~/.config/opencode/skills  # 모든 프로젝트

mkdir -p "$SCOPE"
for s in gorani-ask gorani-change-impact gorani-report gorani-docs-governance gorani-cve-scan gorani-release-check gorani-api-contract-diff gorani-license-notice gorani-release-note gorani-dependency-update gorani-spec-analysis gorani-table-spec gorani-site-structure; do ln -s ~/gorani/skills/$s "$SCOPE/$s"; done
```

Claude Code — 같은 방식으로 위치만 바꿉니다.

```bash
SCOPE=.claude/skills          # 프로젝트에만
# SCOPE=~/.claude/skills      # 모든 프로젝트

mkdir -p "$SCOPE"
for s in gorani-ask gorani-change-impact gorani-report gorani-docs-governance gorani-cve-scan gorani-release-check gorani-api-contract-diff gorani-license-notice gorani-release-note gorani-dependency-update gorani-spec-analysis gorani-table-spec gorani-site-structure; do ln -s ~/gorani/skills/$s "$SCOPE/$s"; done
```

opencode는 Claude 호환 경로(`.claude/skills`, `~/.claude/skills`)도 읽으므로, Claude Code 위치에 한 번만 설치해도 둘 다 사용할 수 있습니다. 설치 후 에이전트를 실행하면 스킬 목록에 열세 스킬이 보입니다.

## 도구 자동 설치

모든 스킬은 필요한 프로그램이 없으면 자동 설치를 시도합니다.

- OS 패키지 관리자(`brew`, `apt-get`, `dnf`, `pacman`, `winget`, `choco`, `scoop`)와 언어 패키지 관리자(`uv`, `pipx`, `npm`, `cargo`, `go`)를 우선합니다.
- 작업에 필요한 도구만 설치하고, 무관한 패키지나 전체 도구 묶음은 설치하지 않습니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 거부하면 설치하지 않고 대체 도구나 입력 파일을 요청합니다.
- 사용자 권한 설치를 우선하고, `sudo`가 필요하면 `sudo -n`으로만 시도합니다. 암호 입력을 요구하지 않습니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 설치는 금지합니다.
- 설치 후 `command -v`와 `--version`으로 확인하고, 실패하면 대체 도구나 입력 파일을 요청합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 문서·고객 데이터를 설치 과정에서 외부로 보내지 않습니다.

## 프롬프트로 쓰기

저장소를 설치하지 않고 raw URL에서 `SKILL.md`를 받아 프롬프트로 넘깁니다. 아래 예시의 `S` 값만 바꾸면 다른 스킬을 실행합니다. `S`에는 `gorani-ask`, `gorani-change-impact`, `gorani-report`, `gorani-docs-governance`, `gorani-cve-scan`, `gorani-release-check`, `gorani-api-contract-diff`, `gorani-license-notice`, `gorani-release-note`, `gorani-dependency-update`, `gorani-spec-analysis`, `gorani-table-spec`, `gorani-site-structure`을 넣습니다.

PowerShell은 한글 인코딩을 위해 아래 프리픽스를 붙이고 `irm` 대신 `curl.exe`를 씁니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
```

opencode — 프롬프트는 위치 인자로 넘깁니다. `-p`는 password 플래그라 쓰지 않습니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="gorani-docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); opencode run "$p"
```

```bash
S=gorani-docs-governance
opencode run "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md)"
```

Claude Code — `-p`는 print(비대화형) 모드입니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="gorani-docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); claude -p "$p"
```

```bash
S=gorani-docs-governance
claude -p "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md)"
```

Codex — 비대화형 실행은 `exec`입니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="gorani-docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); codex exec "$p"
```

```bash
S=gorani-docs-governance
codex exec "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md)"
```

다른 CLI는 공식 문서에서 비대화형 모드를 확인하세요. 프롬프트를 인자로 받지 않으면 stdin 파이프(`echo "$p" | <cli>`)를 씁니다.

opencode에서 권한 프롬프트를 매번 승인하기 번거로우면 `--auto`를 쓸 수 있습니다. 명시적으로 거부하지 않은 모든 권한을 자동 승인하므로 신뢰하는 환경에서만 사용하세요.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="gorani-docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); opencode run --auto "$p"
```

## 결과물 예시

`samples/`에 입력 JSON과 생성 결과를 함께 두었습니다. 같은 입력으로 다시 만들 수 있습니다.

| 파일 | 내용 |
| --- | --- |
| `samples/cve-scan/cve-report-sample.xlsx` | VEX 엑셀 (요청 시 생성, 요약·VEX 판정·원본 findings·실행 로그) |
| `samples/cve-scan/cve-report-sample.vex.json` | OpenVEX JSON (요청 시 생성) |
| `samples/release-check/release-check-sample.xlsx` | 릴리스 점검 엑셀 (요약, 점검 항목, 변경 파일, 커밋, 실행 로그) |
| `samples/license-notice/third-party-notices.html` | 앱에 넣는 자기완결 고지 페이지 (검색, 라이선스 전문 접기) |
| `samples/license-notice/third-party-notices.md` | 같은 내용의 평문 |
| `samples/license-notice/third-party-notices-review.md` | 검토 필요 목록 (내부용, 배포 제외) |
| `samples/release-note/release-notes.html` | 고객용 릴리스 노트 페이지 |
| `samples/release-note/release-notes.md` | 고객용 긴 버전 (GitHub Release·문서) |
| `samples/release-note/release-notes-short.txt` | 스토어 짧은 버전 (기본 500자) |
| `samples/release-note/release-notes-store.txt` | 스토어 긴 버전 (기본 4,000자) |
| `samples/release-note/release-notes-internal.md` | commit 매핑·검토 기록 (내부용, 배포 제외) |
| `samples/spec-analysis/` | 기획서 분석 패키지 (source, index, glossary, domain, processes, flows, validation) |
| `samples/api-contract-diff/` | OpenAPI 이전·새 스펙과 계약 변경 리포트 |
| `samples/table-spec/` | DDL과 테이블 명세서 Excel·Markdown 샘플 |
| `samples/site-structure/` | 실제 레이아웃 인벤토리와 사이트 구조도 Excel·Markdown·HTML 샘플 |
| `samples/change-impact/` | sidecar manifest 예시, PR path-filter 워크플로, stale·full 리포트 샘플 |
| `samples/report/` | `gorani-report`가 만드는 오류·Excel 양식 제안 이슈 본문 샘플 |

샘플 데이터는 형식 설명용 가상 데이터입니다. 재생성 명령은 `samples/README.md`에 있습니다.

## 스킬 추가

1. `skills/gorani-<이름>/SKILL.md`를 만듭니다. frontmatter의 `name`은 `gorani-<이름>`으로 폴더명과 같게, `description`은 언제 쓰는지를 앞세워 1-1024자로 씁니다. 스킬 ID 충돌을 피하기 위해 `gorani-` prefix를 붙입니다.
2. 본문은 H1 + 역할 한 줄로 시작하고 `## 전제`, `## 절차`, `## 출력 형식`, `## 실패 처리`, `## 금지` 같은 섹션을 둡니다.
3. 한국어로 쓰고, 코드 펜스 없이 인라인으로 표기하며, 다른 스킬이나 저장소 밖 파일을 참조하지 않습니다.
4. 보조 스크립트가 필요하면 `skills/gorani-<이름>/scripts/`에 둡니다.
5. 위 스킬 표에 한 줄 추가합니다.

## 저장소 구조

```
skills/gorani-<이름>/SKILL.md      스킬 본문
skills/gorani-<이름>/scripts/      스킬 전용 스크립트
samples/<스킬>/                    예시 입력과 결과물
```

## 문제 해결

| 증상 | 확인 |
| --- | --- |
| 스킬 목록에 안 보임 | `SKILL.md` 대문자 여부, frontmatter의 `name`이 폴더명과 같은지, 같은 이름의 스킬이 여러 위치에 있는지 |
| 루트 `.md`가 `docs/`로 이동함 | gorani-docs-governance가 문서 세트 외 `.md`를 옮긴 것. 스킬 폴더는 대상이 아님 |
| gorani-cve-scan이 도구가 없다고 함 | 스킬이 `## 도구 설치` 원칙에 따라 자동 설치를 시도. 실패하면 표시된 명령으로 수동 설치 후 재실행 |
| gorani-license-notice가 syft가 없다고 함 | 스킬이 자동 설치를 시도. 실패하면 표시된 명령으로 수동 설치 후 재실행. 수집기는 SBOM을 직접 만들지 않음 |
| VEX 엑셀 생성 실패 | VEX 보고서를 요청한 경우에만 openpyxl 필요. 요청하지 않았으면 생성하지 않으며, 필요할 때 스킬이 자동 설치를 시도 |
| gorani-release-check가 ref를 못 찾음 | 브랜치면 `git fetch origin`, 태그·리비전이면 `git fetch --tags origin` 후 ref 확인. 없으면 추측하지 말고 중단 |
| gorani-license-notice에서 라이선스 전문이 비어 있음 | 대상 패키지가 설치되어 있는지 확인. `npm ci --omit=dev` 후 재수집. 원본에 LICENSE가 없으면 입력 JSON에 원문을 넣거나 검토 목록에 남김 |
| HTML이 앱 WebView에서 안 열림 | 파일을 앱 자산에 실제로 복사했는지, CSP·WebView의 JavaScript 설정 확인. 검색만 안 되고 목록은 보여야 정상 |
| `--xlsx`에서 openpyxl 오류 | 선택한 다른 형식은 이미 생성됨. 엑셀이 필요할 때만 스킬이 자동 설치를 시도 |
| gorani-release-note가 이전 태그를 못 찾음 | `git tag`로 릴리스 태그를 확인하고 `--from`을 지정. 태그가 없으면 임의로 만들지 않음 |
| gorani-release-note `--strict`에서 note/reason 오류 | 포함 commit에는 `note`, 제외 commit에는 `reason`을 채움. 수집 직후에는 비어 있음 |
| 스토어 요약 글자 수 초과 | `short_summary`·`store_summary`를 줄이거나 `limits`를 조정. 제출 화면의 실제 제한을 확인 |
| gorani-dependency-update에서 프레임워크 관리 판정이 애매함 | peerDependencies, BOM, SDK manifest, 공식 업데이트 도구를 근거로 삼고, 근거가 없으면 관리하지 않는 것으로 두고 가정을 기록 |
| gorani-dependency-update에서 CVE 도구가 없음 | 자동 설치를 시도하고, 실패하면 `osv-scanner` 또는 OSV API로 확인. 둘 다 불가능하면 "CVE 미확인"으로 남기고 없음으로 단정하지 않음 |
| gorani-dependency-update 모드 3에서 peer 충돌 | `--force` 금지. 프레임워크 패밀리를 함께 올리거나 모드 1로 되돌리고 충돌 패키지를 보고 |
| gorani-spec-analysis 변환 도구가 없음 | 스킬이 자동 설치를 시도. 실패하면 사용자가 markdown·텍스트를 제공할 수 있음 |
| 스캔 PDF가 변환되지 않음 | OCR 도구나 원문 텍스트를 요청. 인식되지 않은 내용을 추측하지 않음 |
| HWP가 변환되지 않음 | `hwp5txt` 자동 설치를 시도하고, 실패하면 LibreOffice로 DOCX 변환 후 `pandoc` 사용 |
| Mermaid 플로우차트가 렌더링되지 않음 | 노드를 줄이고 문법을 단순화. `mmdc` 자동 설치를 시도하고, 실패하면 소스만 남기고 렌더링 미실행을 명시 |

## 라이선스

MIT License. [LICENSE](LICENSE) 파일을 참고하세요.
