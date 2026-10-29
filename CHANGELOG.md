# 변경 이력

최신 버전은 3.7.0(2026-10-29)입니다. 3.7.0 이전 이력은 git log와 태그로 확인합니다.

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
