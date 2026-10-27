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

### gorani-docs-governance

| 항목 | 내용 |
| --- | --- |
| 문서 세트 | 루트 6종 + `.github` 5종 = 11종 |
| 보존 | 기존 문서 삭제·전면 교체 금지, 누락 섹션만 보강 |
| 금지 | 확인 전 LICENSE 선택, 신고 연락처·CODEOWNERS 핸들 생성 |
| 검증 | scratch 저장소에서 11종 생성과 필수 섹션 확인 |

### gorani-cve-scan

| 항목 | 내용 |
| --- | --- |
| 명령 | `syft dir:.`, `osv-scanner scan source -r`, `trivy fs`, `grype sbom:` |
| 종료 코드 | osv-scanner는 취약점 발견 시 1, trivy·grype는 옵션 없이 발견해도 0 |
| VEX 기본값 | 수정 버전이 있으면 `affected`, 없으면 `under_investigation`. 근거 없는 `not_affected` 금지 |
| VEX 보고서 | 사용자 요청 시에만 xlsx·OpenVEX 생성. 요청 없으면 스캔 요약·조치 목록만 만들고 openpyxl 없이 동작 |
| 스크립트 | `scripts/vex_xlsx.py`, openpyxl만 사용, 입력 JSON과 시트 구성 유지 |
| 검증 | 샘플 lockfile로 네 도구 실행 + 요청 시 xlsx·OpenVEX 생성 확인 |

### gorani-release-check

| 항목 | 내용 |
| --- | --- |
| 비교 기준 | `git merge-base` 기반 `main...develop`, 브랜치가 없으면 추측하지 말고 중단 |
| 우선순위 | P0는 배포 차단 사유가 명확할 때만 |
| 배치 | `dev` 항목은 항상 QA 아래 하단, `scripts/release_xlsx.py`가 정렬 강제 |
| 스크립트 | openpyxl만 사용, 입력 JSON과 시트 구성 유지 |
| 검증 | 샘플 JSON으로 xlsx 생성 후 시트 순서·ID·집계 확인 |

### gorani-license-notice

| 항목 | 내용 |
| --- | --- |
| 수집 | `syft` CycloneDX + 설치된 패키지의 LICENSE·NOTICE. npm·pnpm·pub·python 경로만 자동 수집 |
| 기본 출력 | 자기완결 HTML + md. 외부 CSS·JS·폰트·이미지 금지, CSP `default-src 'none'` |
| 산출물 선택 | `--formats html,md,review,xlsx`. 기본 `html,md,review`. xlsx는 선택 시에만 openpyxl 사용 |
| 검토 분리 | copyleft·복수 라이선스·unknown·전문 없음·dev 는 `-review.md`(필요 시 xlsx). HTML·md 에 내부 사유 금지 |
| 분류 | none/notice/weak/strong/network/unknown, OR=약한 쪽, AND=강한 쪽 |
| 스크립트 | `scripts/collect_licenses.py`, `scripts/notice_build.py`. HTML·md 는 표준 라이브러리만, xlsx는 `--formats xlsx` 또는 `--xlsx` + openpyxl |
| 검증 | 샘플 입력으로 HTML·md·review 생성, 외부 요청 0건, 검토 파일 미포함 확인 |

### gorani-release-note

| 항목 | 내용 |
| --- | --- |
| 수집 | `scripts/collect_changes.py` — `git log --no-merges`, conventional commit·키워드로 분류 제안, 내부 변경은 제외 후보 |
| 기본 출력 | `release-notes.md`, `.html`, `-short.txt`(기본 500자), `-store.txt`(기본 4,000자), `-internal.md` |
| 산출물 선택 | `--formats html,md,short,store,internal`. 기본 전체. 선택한 형식만 생성·갱신 |
| 고객 문구 | 이점 중심, 내부 용어·commit hash·이슈 번호·직원 이름·내부 URL 금지, 보안 상세 금지 |
| 검토 분리 | commit 매핑과 제외 사유는 `-internal.md` 에만. 고객 md·html·txt 에 넣지 않음 |
| 스크립트 | `scripts/notes_build.py`, 표준 라이브러리만. 앱스토어 제한은 입력 `limits` 로 조정 |
| 검증 | 샘플 입력으로 고객용·내부용 생성, `--strict`, 글자 수, 외부 리소스 0건 확인 |

### gorani-dependency-update

| 항목 | 내용 |
| --- | --- |
| 모드 | 1 언어·프레임워크 최신 안정화(기본), 2 CVE 최소 수정(프레임워크 패치와 비교), 3 전체 최신 안정 |
| 선택 기준 | 1 호환성 우선·패스트 팔로워, 2 CVE 보완·override 관리 부담, 3 최신화·호환성 테스트 필수 |
| 관리 판정 | peerDependencies, BOM, SDK manifest, constraints, 공식 업데이트 도구를 근거로 기록. 근거가 없으면 비관리로 두고 가정을 명시 |
| 적용 | 해당 생태계의 네이티브 패키지 매니저 사용. lockfile 직접 편집·`--force` 금지 |
| 검증 | install/build/test/lint/typecheck, audit 재확인, lockfile diff, 프레임워크 진단 |
| 금지 | 확인 없는 모드 3, 프레임워크 관리 무단 갱신, CVE 재정의 은폐, 자동 커밋·푸시 |

### gorani-spec-analysis

| 항목 | 내용 |
| --- | --- |
| 변환 | 로컬 도구로 PDF·DOCX·PPTX·HWP·XLSX·Markdown을 `source.plain.md`(단순)와 `source.md`(추적)로 변환. 원본 보존, 페이지·슬라이드 손실 warnings 기록 |
| 보존 | 변환 원문 보존을 `both`/`plain`/`trace`/`none`으로 확인. `none`이면 임시 변환 후 삭제하고 `index.md`에 기록 |
| 수준 | ID·링크 작업을 `full`/`ids`/`none`으로 확인. `full`은 의미 ID·문서 지도·Index·상호 링크·검사 수행 |
| 분석 | `glossary`, `domain`, `processes`, `flows`, `validation` 생성. 사실·추론·질문을 분리하고 원문 위치를 인용 |
| ID | `V/P/F-{AREA}-{TOPIC}-{NN}` 형식. 심각도를 ID에 넣지 않고, `index.md`에 AREA 코드·개수와 Finding/Process/Flow Index를 기록 |
| 링크 | 문서 상단 지도, `index.md`의 Finding/Process/Flow Index, 상대 링크·앵커. `scripts/check_links.py`로 검사하고 깨진 링크가 있으면 완료로 보고하지 않음 |
| 검증 | blocker/major/minor/question 심각도, 추적성, 준비 상태 `ready`/`conditional`/`blocked` |
| 금지 | 원문에 없는 규칙 생성, 외부 OCR·LLM 무단 업로드, AS-IS/TO-BE 혼합, 확인 없는 커밋·푸시 |

## 4. 스킬 형식

- frontmatter: `name`(`gorani-` prefix를 붙인 폴더명과 동일, 소문자·숫자·하이픈), `description`(1-1024자, 언제 쓰는지 중심)
- 새 스킬 ID는 `gorani-` prefix를 붙여 다른 설치본과의 충돌을 피함
- 본문: H1 + 역할 한 줄 → `## 전제`, `## 절차`, `## 출력 형식`, `## 실패 처리`, `## 금지` 같은 섹션
- 한국어, 코드 펜스 없는 인라인 표기
- 다른 스킬이나 저장소 밖 파일을 참조하지 않는 자체 완결 지시문
- 스크립트는 `skills/gorani-<이름>/scripts/`에만 둠

## 5. 도구 자동 설치

모든 스킬은 필요한 프로그램이 없으면 자동 설치를 시도합니다.

- OS 패키지 관리자(macOS `brew`, Debian/Ubuntu `apt-get`, Fedora `dnf`, Arch `pacman`, Windows `winget`·`choco`·`scoop`)와 언어 패키지 관리자(`uv`·`pipx`·`npm`·`cargo`·`go`)를 우선합니다.
- 작업에 필요한 도구만 설치합니다. 무관한 패키지나 전체 도구 묶음을 설치하지 않습니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 설치를 거부하면 설치하지 않고 대체 도구나 입력 파일을 요청합니다.
- 사용자 권한 설치를 우선합니다. `sudo`가 필요하면 `sudo -n`으로만 시도하고 암호 입력을 요구하지 않습니다. 실패하면 실행할 명령과 이유를 보고합니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 다운로드·실행을 금지합니다.
- 설치 후 `command -v`와 `--version`으로 확인합니다. 실패하면 대체 도구를 쓰거나 입력 파일을 요청합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 문서·고객 데이터를 설치 과정에서 외부로 보내지 않습니다.
- GUI 앱·드라이버·커널·서비스처럼 시스템 변경이 큰 설치는 먼저 확인합니다.
- 각 스킬의 `## 도구 설치` 절은 이 장을 스킬에 맞게 풀어 쓴 것입니다. 충돌하면 이 장을 우선합니다.

## 6. 검증과 기록

- 스킬·스크립트 변경은 실제로 실행해 확인합니다. 코드를 읽고 판단한 것은 검증으로 치지 않습니다.
- 실행한 명령, 결과, 확인하지 못한 부분을 `.omo/evidence/YYYY-MM-DD-<주제>.md`에 적습니다.
- `.omo/`는 커밋하지 않습니다.

## 7. 하지 말 것

- 지시 없는 커밋·푸시
- `.omo/`, `.codegraph/`, `.idea/`, `.security/`, `.qa/`, `__pycache__/`, `*.pyc` 커밋
- README 명령 구조 변경: `opencode run` positional, `claude -p`, `codex exec`, `curl.exe` + UTF-8 프리픽스
- 확인하지 않은 내용을 문서에 단정적으로 쓰기
- `curl | sh`, 출처 불명 바이너리, 임의 URL로 도구 설치
- 무관한 패키지·전체 도구 묶음 설치
- 설치 과정에서 문서·고객 데이터를 외부로 전송

## 8. 변경 기록

| 날짜 | 변경 | 기록 |
| --- | --- | --- |
| 2026-10-27 | README·AGENTS·CHANGELOG를 새 양식으로 재작성 | - |
| 2026-10-27 | `license-notice` 추가 (HTML 고지 페이지, 검토 목록 분리) | `.omo/evidence/2026-10-27-license-notice.md` |
| 2026-10-27 | `release-note` 추가 (고객용 HTML·md·스토어 요약, 내부 매핑) | `.omo/evidence/2026-10-27-release-note.md` |
| 2026-10-28 | `dependency-update` 추가 (3모드, 생태계별 수동 절차) | `.omo/evidence/2026-10-28-dependency-update.md` |
| 2026-10-28 | 모든 스킬 ID에 `gorani-` prefix 적용 (v3.0.0) | `.omo/evidence/2026-10-28-skill-rename.md` |
| 2026-10-28 | `gorani-spec-analysis` 추가 (기획서 md 변환·용어·도메인·프로세스·플로우·검증, 의미 기반 ID·문서 링크) | `.omo/evidence/2026-10-28-spec-analysis.md` |
| 2026-10-28 | `source.plain.md`·원문 보존 선택 추가 (v3.2.0) | `.omo/evidence/2026-10-28-spec-analysis.md` |
| 2026-10-28 | 모든 스킬에 도구 자동 설치 원칙 추가 (v3.3.0) | `.omo/evidence/2026-10-28-tool-install.md` |
