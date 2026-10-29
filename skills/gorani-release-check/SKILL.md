---
name: gorani-release-check
description: 운영 배포 전 브랜치 또는 두 리비전 사이의 차이를 분석해 기능 점검 엑셀 보고서를 만든다. P0/P1/P2 우선순위와 QA/개발자 전용 구분을 적용하고, 개발자 전용 항목은 시트 하단에 배치한다. 릴리스 전 최종 점검, 배포 리스크 확인, 브랜치 간 변경 리뷰, 태그·커밋 리비전 비교가 필요할 때 사용.
---

# 릴리스 전 diff 점검

브랜치 간 차이 또는 두 리비전 사이의 차이를 근거로 배포 전 점검 항목을 만들고, 엑셀 보고서로 정리합니다. 코드는 수정하지 않습니다.

## 전제

- git 저장소여야 합니다.
- 브랜치 모드의 기본값은 `origin/main`(기준)과 `origin/develop`(대상)입니다.
- 브랜치 이름이 다르면 사용자에게 확인합니다. 예: `master`, `release/1.2`, `dev`
- 리비전 모드는 태그, 커밋 해시, `HEAD~3`, 날짜 표현 등 `git rev-parse`로 확인 가능한 ref를 받습니다.
- 배포 버전이나 릴리스 노트가 있으면 요약 시트에 함께 기록합니다.

## 비교 모드

| 모드 | 비교 범위 | 명령 | 용도 |
| --- | --- | --- | --- |
| branch-merge-base | 공통 조상 → 대상 브랜치 | `--mode branch` | 기본 브랜치 diff |
| branch-tip | 기준 브랜치 tip → 대상 브랜치 tip | `--mode branch --tip` | tip 대 tip 비교 |
| revision | 시작 ref → 대상 ref | `--mode revision --from REF --to REF` | 태그·커밋 직접 비교 |
| revision-merge-base | 두 ref의 공통 조상 → 대상 ref | `--mode revision --from REF --to REF --merge-base` | 갈라진 리비전 비교 |

`..`와 `...`의 의미:

- `A..B`는 B에만 있는 변경, 즉 tip 대 tip 비교입니다.
- `A...B`는 A와 B의 공통 조상에서 B까지의 변경입니다.
- 브랜치 모드는 기본적으로 merge-base를 쓰고, 리비전 모드는 기본적으로 직접 비교합니다.

## 절차

1. 비교 모드를 확인합니다. 브랜치 비교인지, 리비전 비교인지, merge-base가 필요한지 사용자에게 확인합니다.
2. ref를 확인합니다.
   - 브랜치 모드: `git fetch origin --prune`, `git rev-parse --verify origin/main`, `git rev-parse --verify origin/develop`
   - 리비전 모드: 필요하면 `git fetch --tags origin`, `git rev-parse --verify <ref>^{commit}`
   - ref가 없으면 추측하지 말고 보고 후 중단합니다.
3. 비교 컨텍스트를 만듭니다.

   `python3 <스킬 폴더>/scripts/compare_revisions.py --mode branch --base origin/main --head origin/develop --out .qa/release-check-input.json`

   리비전 비교:

   `python3 <스킬 폴더>/scripts/compare_revisions.py --mode revision --from v1.0.0 --to v1.2.0 --out .qa/release-check-input.json`

   옵션:
   - 브랜치 tip 대 tip: `--tip`
   - 리비전 공통 조상: `--merge-base`
   - fetch 생략: `--no-fetch`
   - 프로젝트명·배포 버전: `--project`, `--release-version`

   스크립트는 `comparison_mode`, `base`, `head`, `merge_base`, `stats`, `commits`, `files`, `logs`를 채우고 `items`는 빈 배열로 둡니다.

4. 변경을 분류합니다: 기능, API 계약, DB·마이그레이션, 설정·환경변수, 의존성, 보안·인증, UI, 배포·인프라, 문서.
5. 점검 항목을 도출합니다. 변경마다 "무엇을 확인해야 하는가"를 실행 가능한 문장으로 작성하고, 기대 결과와 변경 근거(파일 경로·커밋)를 함께 기록합니다.
6. 우선순위를 지정합니다.
   - P0: 배포 차단. 데이터 손상·유실, 인증·결제·권한, 핵심 사용자 흐름 중단, 마이그레이션 실패, 롤백 불가
   - P1: 주요 기능 오동작, 회귀, 성능 저하, API 계약 변경, 설정 누락
   - P2: 경미한 UI·문구, 내부 리팩터링, 로그·주석, 문서
7. 구분을 지정합니다.
   - `qa`: 화면, API 호출, CLI 실행처럼 외부에서 확인 가능한 항목
   - `dev`: 코드 리딩, 로그, DB 상태, 설정, 마이그레이션, 동시성, 예외 처리처럼 코드·내부 지식이 필요한 항목
8. `.qa/release-check-input.json`의 `items`를 채웁니다. 스크립트가 만든 `stats`·`commits`·`files`·`logs`는 근거로 유지합니다.
9. 보고서를 생성합니다.

   `python3 <스킬 폴더>/scripts/release_xlsx.py --input .qa/release-check-input.json --outdir docs/qa`

10. 요약 보고: P0/P1/P2 건수, 개발자 전용 건수, 확인이 필요한 항목, 비교 방식과 비교 기준을 보고합니다.

## 엑셀 보고서

스크립트가 점검 항목을 정렬해 엑셀 워크북으로 만듭니다. 개발자 전용 항목은 항상 QA 항목 아래, 시트 하단에 배치됩니다.

- 스크립트 위치: 이 스킬 폴더의 `scripts/release_xlsx.py`, `scripts/compare_revisions.py`
- 출력: `docs/qa/release-check-YYYY-MM-DD.xlsx`
- 시트 구성
  - 요약: 프로젝트, 배포 버전, 비교 방식, 비교 기준, merge-base, 커밋·파일·증감 라인 수, P0/P1/P2 집계, QA·개발자 건수, 확인 결과 집계
  - 점검 항목: QA 항목(P0→P2) → "개발자 전용 점검" 구분 행 → 개발자 항목(P0→P2)
  - 변경 파일: 경로, 상태(A/M/D/R), 증감 라인, 영역, 관련 항목 ID
  - 커밋: 해시, 날짜, 작성자, 제목
  - 실행 로그: 명령, 종료 코드, 상태, 비고

점검 항목 열: ID, 우선순위, 영역, 점검 항목, 기대 결과, 변경 근거, 구분, 확인 결과, 확인자, 확인일, 비고

- 확인 결과는 `미확인`, `통과`, `실패`, `해당 없음` 중 하나이며 기본값은 `미확인`
- ID 규칙: `P0-QA-01`, `P0-DEV-01` 처럼 우선순위·구분별로 부여

## 입력 JSON

`compare_revisions.py`가 만드는 필드:

- `project`: 프로젝트명
- `release_version`: 배포 버전 (선택, 스크립트 옵션)
- `comparison_mode`: `branch-merge-base`, `branch-tip`, `revision`, `revision-merge-base`
- `base`, `head`: 비교 기준·대상 ref
- `base_commit`, `head_commit`: 확인된 커밋 해시
- `merge_base`: 공통 조상 해시. 직접 비교면 빈 문자열
- `generated_at`: 생성 시각 (ISO 8601)
- `stats`: `commits`, `files`, `additions`, `deletions`
- `commits`: `hash`, `date`, `author`, `subject`
- `files`: `path`, `old_path`(리네임 시), `status`, `additions`, `deletions`, `area`, `related_items`
- `items`: 점검 항목. 에이전트가 채움
- `logs`: `command`, `exit_code`, `status`, `note`

`items` 필드:

- `priority`(P0/P1/P2), `audience`(qa/dev), `area`, `item`, `expected`, `evidence`, `status`, `owner`, `checked_at`, `note`

## 작성 규칙

- 점검 항목은 한 문장으로 실행 가능하게 작성합니다. 예: "비밀번호 재설정 메일 링크가 24시간 후 만료되는지 확인"
- 기대 결과는 판정 가능한 형태로 작성합니다. 예: "만료 후 링크 접근 시 오류 메시지 표시"
- 변경 근거에는 diff에 등장하는 파일 경로를 포함합니다.
- diff에 없는 내용은 점검 항목으로 만들지 않습니다.
- P0는 배포 차단 사유가 명확할 때만 사용합니다.
- 리비전 비교에서 시작 ref가 대상 ref의 조상이면 `revision`과 `revision-merge-base` 결과가 같을 수 있습니다. 그래도 비교 방식을 요약에 기록합니다.
- 변경이 없으면 빈 목록과 "변경 없음"을 보고합니다. 점검 항목을 억지로 만들지 않습니다.

## 전제 도구

python3와 openpyxl이 필요합니다. `compare_revisions.py`는 표준 라이브러리와 git만 사용합니다. openpyxl이 없으면 아래 `## 도구 설치` 원칙에 따라 자동 설치를 시도합니다.

## 도구 설치

필요한 프로그램이 없으면 자동 설치를 시도합니다.

- OS 패키지 관리자(macOS `brew`, Debian/Ubuntu `apt-get`, Fedora `dnf`, Arch `pacman`, Windows `winget`·`choco`·`scoop`)와 언어 패키지 관리자(`uv`·`pipx`·`npm`·`cargo`·`go`)를 우선합니다.
- 작업에 필요한 도구만 설치합니다. 무관한 패키지나 전체 도구 묶음을 설치하지 않습니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 설치를 거부하면 설치하지 않고 대체 도구나 입력 파일을 요청합니다.
- 사용자 권한 설치를 우선합니다. `sudo`가 필요하면 `sudo -n`으로만 시도하고 암호 입력을 요구하지 않습니다. 실패하면 실행할 명령과 이유를 보고합니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 다운로드·실행을 금지합니다.
- 설치 후 `command -v`와 `--version`으로 확인합니다. 실패하면 대체 도구를 쓰거나 입력 파일을 요청합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 문서·고객 데이터를 설치 과정에서 외부로 보내지 않습니다.
- GUI 앱·드라이버·커널·서비스처럼 시스템 변경이 큰 설치는 먼저 확인합니다.

## 금지

- 코드·설정 수정, 커밋, 푸시 금지 (점검 보고서만 생성)
- 확인하지 않은 변경을 사실처럼 단정하지 말 것. 근거가 없으면 제외하거나 질문
- 개발자 전용 항목을 QA 항목 사이에 섞지 말 것. 시트 하단 배치 규칙 유지
- P0를 습관적으로 붙이지 말 것. 배포 차단 사유를 함께 적을 수 없으면 P1 이하로 내림
- ref가 없는데 다른 브랜치·태그·커밋으로 대체해 추측하지 말 것
- 리비전 비교에서 `..`와 `...`를 섞어 설명하지 말 것. 사용한 비교 방식을 요약과 보고서에 명시
