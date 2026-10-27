# 변경 이력

최신 버전은 2.1.0(2026-10-27)입니다. 2.1.0 이전 이력은 git log와 태그로 확인합니다.

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
