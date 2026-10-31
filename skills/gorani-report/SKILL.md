---
name: gorani-report
description: gorani 스킬 사용 중 만난 오류·개선·아이디어·양식 제안을 GitHub 이슈로 정리해 올린다. 실행 명령·오류 로그·환경을 모아 민감 정보를 마스킹하고 중복 이슈를 확인한다. 공개 이슈 작성 전 사용자 확인을 받아야 할 때 사용.
metadata:
  version: "3.17.0"
  updated: "2026-10-31"
---

# 스킬 문제 보고

gorani 스킬을 쓰다 만난 오류뿐 아니라 **개선·아이디어·Excel/HTML/Markdown 양식 제안**을 공개 GitHub 이슈로 정리합니다. 사용자가 로그를 모으거나 양식을 맞출 필요 없이, 스킬 이름·버전·실행 명령·오류·제안 내용·환경을 모아 드래프트를 만들고, 사용자 확인을 받은 뒤 `allbegray/gorani`에 이슈를 만듭니다.

## 전제

- 기본 대상 저장소는 `allbegray/gorani`입니다. 포크나 다른 저장소는 `--repo` 또는 `GORANI_REPORT_REPO` 환경변수로 바꿉니다.
- 이 저장소에는 gorani 스킬·스크립트 문제만 보고합니다. 사용자 프로젝트의 애플리케이션 버그는 해당 프로젝트 저장소에 보고합니다.
- `gh`가 설치되어 있고 `gh auth login`으로 인증되어 있어야 실제 이슈를 만들 수 있습니다.
- `gh`가 없거나 인증되지 않았으면 드래프트만 만들고 설치·인증 방법을 안내합니다. 인증을 대신 진행하지 않습니다.
- GitHub 이슈는 공개됩니다. 고객 정보, 시크릿, 내부 URL, 개인 이메일, 실제 운영 데이터를 넣지 않습니다.
- 오류가 아니어도 됩니다. 아이디어·양식·문서 제안은 재현 절차나 오류 로그 없이 제안 내용과 기대 효과만으로 충분합니다.
- 기본은 드래프트 생성입니다. `--create` 또는 `--comment-on`을 명시하고, 사용자 확인을 받은 뒤에만 실제로 씁니다.
- 드래프트는 `.gorani/report/`에 만들고 커밋하지 않습니다.
- 스킬 버전은 대상 `SKILL.md`의 `metadata.version`·`metadata.updated`를 읽어 본문에 넣습니다. 없으면 `unknown`으로 두고 `--skill-version`으로 보정할 수 있습니다.
- Python 3 표준 라이브러리만 사용합니다. `gh`와 `git`은 선택이 아니라 실제 생성·환경 수집에 필요합니다.

## 절차

1. 종류를 고릅니다.
   - `bug`: 스킬이 실패하거나 결과가 잘못됨
   - `enhancement`: 있으면 좋을 기능·개선
   - `idea`: 새로운 아이디어·기능 제안
   - `format`: Excel·Markdown·HTML 출력 양식 제안
   - `documentation`: 설명·예시·링크 오류
   - `question`: 사용법이 불명확하거나 확인이 필요함
2. 종류에 맞는 사실만 모읍니다.
   - 공통: 스킬 이름, 한 줄 요약, 스킬 버전, 관련 도구 버전
   - 오류: 기대 결과, 실제 결과, 재현 절차, 실행 명령, 오류 메시지·스택 트레이스
   - 아이디어·개선·양식: 제안 내용, 기대 효과, 현재 동작·양식, 참고 화면·명령
   - 문서: 제안 내용, 현재 문서, 참고 링크
3. 오류 로그는 파일로 남깁니다.

   `python3 <스킬 폴더>/scripts/... 2> .gorani/report/error.log`

4. 드래프트를 만듭니다.

   오류:

   `python3 <스킬 폴더>/scripts/report_issue.py --skill gorani-table-spec --kind bug --summary "..." --expected "..." --actual "..." --steps "..." --command "..." --error-file .gorani/report/error.log --tool "openpyxl=3.1.5"`

   Excel 양식 제안:

   `python3 <스킬 폴더>/scripts/report_issue.py --skill gorani-table-spec --kind format --area excel --summary "..." --proposal "..." --benefit "..." --current "..."`

   새 아이디어:

   `python3 <스킬 폴더>/scripts/report_issue.py --skill gorani-table-spec --kind idea --summary "..." --proposal "..." --benefit "..."`

5. 출력에서 드래프트 경로, 마스킹 내역, 잔여 위험, 중복 후보를 확인합니다.
6. 드래프트 본문을 사용자에게 보여 주고 묻습니다.
   - “이 내용으로 `allbegray/gorani`에 공개 이슈를 만들까요?”
   - 사용자 확인 전에는 `--create`를 실행하지 않습니다.
7. 중복 후보가 있으면 먼저 보여 줍니다.
   - 기존 이슈에 추가 정보를 붙이는 게 맞으면 `--comment-on <번호>`
   - 그래도 새 이슈가 필요하면 `--allow-duplicate`와 함께 `--create`
8. 사용자가 확인하면 실제로 만듭니다.

   `python3 <스킬 폴더>/scripts/report_issue.py ... --create`

9. `gh`가 없거나 인증되지 않았으면 드래프트 경로를 알려 주고 `gh auth login` 또는 드래프트 직접 붙여넣기를 안내합니다.
10. 생성된 이슈 URL을 사용자에게 보고합니다.

## 입력과 옵션

| 옵션 | 내용 |
| --- | --- |
| `--skill` | 대상 스킬 이름. 필수 |
| `--skill-version` | 스킬 버전 override. 기본은 `SKILL.md`의 `metadata.version` |
| `--skill-updated` | 스킬 갱신일 override. 기본은 `SKILL.md`의 `metadata.updated` |
| `--kind` | `bug`(기본), `enhancement`, `idea`, `format`, `documentation`, `question` |
| `--area` | `excel`, `markdown`, `html`, `cli`, `docs`, `other` |
| `--summary` | 한 줄 요약. 필수 |
| `--expected` | 기대 결과. 오류·개선에서 사용 |
| `--actual` | 실제 결과. 아이디어·양식에서는 현재 동작으로도 사용 |
| `--proposal`, `--proposal-file` | 제안 내용. 개선·아이디어·양식·문서 |
| `--benefit`, `--benefit-file` | 기대 효과 |
| `--current`, `--current-file` | 현재 동작·양식 |
| `--steps`, `--steps-file` | 재현 절차 |
| `--command` | 실행한 명령. 민감 정보는 자동 마스킹 |
| `--error`, `--error-file` | 오류 메시지·스택 트레이스 |
| `--context`, `--context-file` | 추가 맥락 |
| `--tool` | 도구 버전. 여러 번 지정 가능 |
| `--repo` | 이슈를 만들 저장소. 기본 `allbegray/gorani` |
| `--out` | 드래프트 경로. `-`이면 파일을 만들지 않고 stdout만 사용 |
| `--json` | 결과를 JSON으로 출력 |
| `--create` | 사용자 확인 후 새 이슈 생성 |
| `--comment-on` | 새 이슈 대신 기존 이슈 번호에 코멘트 |
| `--allow-duplicate` | 중복 후보가 있어도 새 이슈 생성 |
| `--no-duplicate-search` | 중복 검색 생략 |
| `--force` | 잔여 위험 패턴이 있어도 생성. 사용자 확인 후에만 |

## 출력 형식

드래프트는 `.gorani/report/<skill>-<timestamp>.md`에 만듭니다.

본문 구성:

- `## 요약`
- `## 종류`
- `## 영역` (`--area`를 준 경우)
- `## 환경`: 스킬, 스킬 버전, 스킬 갱신일, skill source commit, OS, Python, Shell, 도구 버전
- `## 공개 안전 확인`
- `gorani-report`로 작성했다는 한 줄

종류별 본문:

- 오류: `## 재현 절차`, `## 기대 결과`, `## 실제 결과`, `## 실행 명령`, `## 오류 로그`, `## 추가 맥락`
- 개선·아이디어·양식: `## 제안`, `## 기대 효과`, `## 현재 동작·양식`, `## 참고한 화면·명령`, `## 실행 명령`, `## 참고 로그`
- 문서: `## 제안`, `## 현재 문서`, `## 기대 효과`, `## 참고`
- 질문: `## 질문`, `## 시도한 것`, `## 참고`

`--json`은 아래 필드를 출력합니다.

| 필드 | 내용 |
| --- | --- |
| `repo`, `skill`, `skill_version`, `skill_updated`, `kind`, `title`, `label` | 이슈 메타데이터 |
| `draft` | 드래프트 경로 또는 `-` |
| `body` | 마스킹된 본문 |
| `duplicates` | 중복 후보 `number`, `title`, `url`, `state` |
| `duplicate_error` | 중복 검색을 못 한 사유 |
| `redactions` | 마스킹 규칙별 건수 |
| `risks` | 남은 위험 패턴 |
| `authenticated`, `auth_error` | `gh` 인증 상태 |
| `created`, `commented`, `url` | 실제 생성·코멘트 결과 |
| `error` | 실패 사유 |

## 마스킹과 중복

자동 마스킹 대상:

- 현재 작업 디렉터리와 홈 디렉터리 경로
- `ghp_`, `gho_`, `github_pat_`, `sk-`, `AKIA`, `xox*` 토큰
- JWT, private key
- `password`, `token`, `secret`, `api_key`, `authorization`, `bearer` 값
- 자격증명이 들어간 DB URL
- 이메일 주소
- localhost·사설 IP 내부 URL

마스킹 후에도 private key, 토큰, 자격증명 URL, 이메일, 내부 URL이 남아 있으면 `--create`를 중단합니다. 사용자가 내용을 직접 확인하고 안전하다고 판단한 경우에만 `--force`를 씁니다.

중복 검색은 `gh issue list --search <skill>`로 열린·닫힌 이슈를 함께 봅니다. 중복 후보가 있으면 새 이슈 대신 기존 이슈 코멘트를 먼저 제안합니다.

## 실패 처리

- `gh`가 없으면 드래프트만 만들고 exit 2로 끝냅니다. `gh` 설치와 `gh auth login`을 안내합니다.
- `gh` 인증이 없으면 드래프트만 만들고 exit 2로 끝냅니다. 인증을 대신하지 않습니다.
- 중복 후보가 있는데 `--allow-duplicate`가 없으면 새 이슈를 만들지 않고 exit 1로 끝냅니다. 기존 이슈 코멘트를 제안합니다.
- 잔여 위험 패턴이 있으면 `--force` 없이는 exit 1로 끝냅니다. 드래프트는 남깁니다.
- `--create`가 실패하면 `gh` 오류와 드래프트 경로를 보고합니다. 같은 명령을 반복하기 전에 인증·권한·라벨을 확인합니다.
- `--comment-on`이 실패하면 이슈 번호와 저장소를 확인합니다. 권한이 없으면 드래프트만 남깁니다.
- 오류 로그가 너무 길면 앞뒤만 남기고 중략합니다. 전체 로그가 필요하면 최소 재현 입력으로 줄입니다.
- 대상 스킬의 `SKILL.md`를 찾지 못하거나 `metadata.version`이 없으면 버전을 `unknown`으로 표시합니다. 사용자가 알고 있으면 `--skill-version`으로 보정합니다.
- 아이디어·양식 제안에 재현 절차나 오류 로그가 없어도 실패로 보지 않습니다. 제안 내용과 기대 효과를 우선합니다.
- 스킬 자체가 실행되지 않아 이 스킬도 쓸 수 없으면 `.github/ISSUE_TEMPLATE/skill-report.yml` 양식으로 직접 이슈를 만듭니다.

## 도구 설치

- `gh`가 없으면 OS 패키지 관리자로 설치를 시도합니다.
  - macOS: `brew install gh`
  - Debian·Ubuntu: `apt-get install gh`
  - Fedora: `dnf install gh`
  - Arch: `pacman -S github-cli`
  - Windows: `winget install GitHub.cli` 또는 `choco install gh`
- 설치 전에 도구와 명령을 알립니다. 사용자가 거부하면 드래프트만 만들고 직접 붙여넣도록 안내합니다.
- 설치 후 `command -v gh`와 `gh --version`으로 확인합니다.
- `gh auth login`은 사용자가 직접 실행합니다. 토큰을 명령행에 남기지 않습니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 다운로드·실행을 금지합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.

## 금지

- 사용자 확인 없이 공개 이슈를 만들지 않습니다.
- 고객 정보, 시크릿, 내부 URL, 실제 운영 데이터를 이슈에 넣지 않습니다.
- 마스킹 경고를 숨기거나 `--force`로 덮지 않습니다. 사용자가 내용을 확인한 뒤에만 사용합니다.
- 중복 후보를 무시하고 새 이슈를 만들지 않습니다. `--allow-duplicate`는 사용자 확인 후에만 사용합니다.
- `gh auth login`을 대신 실행하거나 토큰을 파일·명령행에 남기지 않습니다.
- `.gorani/report/`를 커밋하지 않습니다.
- 이슈 생성 권한이 없는 저장소에 강제로 쓰지 않습니다.
- 사용자 지시 없이 다른 저장소·조직에 이슈를 만들지 않습니다.
