# 변경 이력

최신 버전은 2.3.0(2026-10-28)입니다. 2.3.0 이전 이력은 git log와 태그로 확인합니다.

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
