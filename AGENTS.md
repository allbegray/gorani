# AGENTS.md

이 저장소에서 작업하는 에이전트의 규칙입니다. 아래 장 번호로 규칙을 인용합니다.

## 1. 저장소

| 항목 | 값 |
| --- | --- |
| 성격 | 실무 반복 작업을 AI CLI 스킬로 묶은 공개 모음집 |
| 배포 | github.com/allbegray/gorani |
| 스킬 형식 | Agent Skills 표준 (`skills/<이름>/SKILL.md`), opencode·Claude Code 공통 |
| 루트 문서 | README, AGENTS, CHANGELOG |

공개 저장소입니다. 실제 고객 정보, 시크릿, 내부 URL, 개인 연락처를 넣지 않습니다.

## 2. 변경 계약

| 바꾸는 것 | 같은 변경에 포함 |
| --- | --- |
| SKILL.md의 절차·출력 | README의 해당 스킬 설명, 출력 형식이 바뀌면 samples 재생성, evidence |
| scripts의 시트·정렬 | samples 재생성, SKILL.md의 입력·시트 설명, evidence |
| 새 스킬 | README 스킬 표, 3장 스킬 계약, samples(선택) |
| 스킬 이름·경로 | README의 설치·프롬프트 명령 경로, 3장 스킬 계약 |

## 3. 스킬 계약

### docs-governance

| 항목 | 내용 |
| --- | --- |
| 문서 세트 | 루트 6종 + `.github` 5종 = 11종 |
| 보존 | 기존 문서 삭제·전면 교체 금지, 누락 섹션만 보강 |
| 금지 | 확인 전 LICENSE 선택, 신고 연락처·CODEOWNERS 핸들 생성 |
| 검증 | scratch 저장소에서 11종 생성과 필수 섹션 확인 |

### cve-scan

| 항목 | 내용 |
| --- | --- |
| 명령 | `syft dir:.`, `osv-scanner scan source -r`, `trivy fs`, `grype sbom:` |
| 종료 코드 | osv-scanner는 취약점 발견 시 1, trivy·grype는 옵션 없이 발견해도 0 |
| VEX 기본값 | 수정 버전이 있으면 `affected`, 없으면 `under_investigation`. 근거 없는 `not_affected` 금지 |
| 스크립트 | `scripts/vex_xlsx.py`, openpyxl만 사용, 입력 JSON과 시트 구성 유지 |
| 검증 | 샘플 lockfile로 네 도구 실행 + xlsx·OpenVEX 생성 확인 |

### release-check

| 항목 | 내용 |
| --- | --- |
| 비교 기준 | `git merge-base` 기반 `main...develop`, 브랜치가 없으면 추측하지 말고 중단 |
| 우선순위 | P0는 배포 차단 사유가 명확할 때만 |
| 배치 | `dev` 항목은 항상 QA 아래 하단, `scripts/release_xlsx.py`가 정렬 강제 |
| 스크립트 | openpyxl만 사용, 입력 JSON과 시트 구성 유지 |
| 검증 | 샘플 JSON으로 xlsx 생성 후 시트 순서·ID·집계 확인 |

## 4. 스킬 형식

- frontmatter: `name`(폴더명과 동일, 소문자·숫자·하이픈), `description`(1-1024자, 언제 쓰는지 중심)
- 본문: H1 + 역할 한 줄 → `## 전제`, `## 절차`, `## 출력 형식`, `## 실패 처리`, `## 금지` 같은 섹션
- 한국어, 코드 펜스 없는 인라인 표기
- 다른 스킬이나 저장소 밖 파일을 참조하지 않는 자체 완결 지시문
- 스크립트는 `skills/<이름>/scripts/`에만 둠

## 5. 검증과 기록

- 스킬·스크립트 변경은 실제로 실행해 확인합니다. 코드를 읽고 판단한 것은 검증으로 치지 않습니다.
- 실행한 명령, 결과, 확인하지 못한 부분을 `.omo/evidence/YYYY-MM-DD-<주제>.md`에 적습니다.
- `.omo/`는 커밋하지 않습니다.

## 6. 하지 말 것

- 지시 없는 커밋·푸시
- `.omo/`, `.codegraph/`, `.idea/`, `.security/`, `.qa/`, `__pycache__/`, `*.pyc` 커밋
- README 명령 구조 변경: `opencode run` positional, `claude -p`, `codex exec`, `curl.exe` + UTF-8 프리픽스
- 확인하지 않은 내용을 문서에 단정적으로 쓰기

## 7. 변경 기록

| 날짜 | 변경 | 기록 |
| --- | --- | --- |
| 2026-10-27 | README·AGENTS·CHANGELOG를 새 양식으로 재작성 | - |
