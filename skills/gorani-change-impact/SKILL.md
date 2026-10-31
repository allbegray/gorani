---
name: gorani-change-impact
description: 기존 산출물이 소스 변경으로 낡았는지 sidecar .artifact.json과 git diff로 값싸게 확인하고, 릴리스 때만 전체 영향도를 정리한다. 산출물을 자동 수정하지 않고 갱신 명령만 제안한다. PR·릴리스 전 산출물 갱신 대상 확인이 필요할 때 사용.
metadata:
  version: "3.17.0"
  updated: "2026-10-31"
---

# 변경 영향 확인

기존 스킬이 만든 산출물 옆의 `*.artifact.json` sidecar manifest와 git diff를 비교해 **갱신이 필요한 산출물**을 알려줍니다. 기본은 값싼 `stale` 모드이고, 화면·API·DB·테스트 영향도는 릴리스 전 `full` 모드에서만 정리합니다. 산출물을 직접 고치지 않고 갱신 명령만 제안합니다.

## 전제

- git 저장소에서 실행합니다.
- 비교할 산출물 옆에 sidecar manifest가 있어야 합니다. 없으면 경고만 하고 넘어갑니다.
- `gorani-site-structure`, `gorani-table-spec`, `gorani-api-contract-diff`는 산출물을 만들 때 manifest를 함께 만듭니다.
- `stale` 모드는 코드를 파싱하지 않습니다. `git diff --name-only`와 글롭 매칭만 사용합니다.
- 갱신 대상이 없으면 리포트 파일도 PR 코멘트도 만들지 않습니다.
- `full` 모드는 릴리스 전이나 사용자가 요청할 때만 실행합니다. 매 PR에 돌리지 않습니다.
- Python 3 표준 라이브러리만 사용합니다. 추가 패키지가 필요하지 않습니다.
- `.gorani/impact/`는 로컬 임시 산출물입니다. 커밋하지 않습니다.

## Sidecar manifest

산출물과 같은 디렉터리에 `<이름>.artifact.json`을 둡니다. 사람이 중앙 목록을 관리하지 않고, 각 스킬이 자기 산출물을 만들 때 갱신합니다.

| 필드 | 내용 |
| --- | --- |
| `version` | manifest 형식 버전. 현재 `1` |
| `skill` | 산출물을 만든 스킬 이름 |
| `artifact` | 대표 산출물 경로 |
| `outputs` | 함께 생성된 산출물 경로 목록 |
| `sources` | 갱신 판단에 쓸 소스 글롭 목록 |
| `generated_commit` | 산출물을 만든 시점의 git commit. manifest가 커밋되면 마지막 커밋과 비교해 더 최신 쪽을 기준으로 사용 |
| `generated_at` | 생성 시각(ISO 8601) |
| `working_tree_dirty` | 생성 시 워킹 트리에 커밋되지 않은 변경이 있었는지 |
| `regenerate` | 산출물을 다시 만드는 명령 |
| `note` | 선택 메모. DB 모드처럼 소스를 자동으로 정할 수 없을 때 사용 |

`sources` 글롭 규칙:

- `*`는 한 경로 구간, `**`는 여러 경로 구간을 뜻합니다.
- `?`는 한 글자, `[...]`는 문자 범위입니다.
- `/`가 없는 패턴은 모든 깊이의 파일명과 비교합니다. 예: `*.sql`
- `!`로 시작하면 제외입니다. 예: `db/migrations/**`, `!db/migrations/archive/**`
- manifest와 `outputs`에 적힌 파일은 변경 목록에서 제외합니다. 산출물을 다시 만들어도 자기 자신 때문에 stale이 되지 않습니다.

`regenerate`의 스크립트 경로는 산출물을 만든 위치를 기준으로 기록합니다. 스킬이 저장소 밖에 설치되어 있으면 `gorani-.../scripts/...` 형태로 기록되므로, 실제 설치 경로에 맞게 바꿔 실행합니다. DB URL 같은 시크릿은 manifest에 실제 값으로 넣지 않습니다.

`outputs`에는 마지막 생성에서 선택한 형식만 담깁니다. 형식 조합을 바꾸면 이전 산출물을 지우거나 같은 조합으로 다시 생성해 manifest와 실제 파일을 맞춥니다.

예시는 `samples/change-impact/artifact-manifest.example.json`에 있습니다.

## 절차

### stale 모드

1. 기존 산출물 옆에 manifest가 있는지 확인합니다. 없으면 해당 스킬로 산출물을 다시 만들어 manifest를 만듭니다.
2. 저장소 루트에서 `python3 <스킬 폴더>/scripts/change_impact.py --mode stale`을 실행합니다. `--mode`를 생략하면 stale입니다.
3. 출력이 없으면 갱신 대상이 없다는 뜻입니다. 파일을 만들지 않고 끝냅니다.
4. stale 판정 기준은 manifest가 마지막으로 커밋된 commit과 `generated_commit` 중 더 최신 commit입니다. 산출물과 manifest를 같은 commit에 넣으면 그 commit 이후 변경만 봅니다. 둘 다 없을 때만 `--base`를 fallback으로 씁니다.
5. 갱신 대상이 있으면 `.gorani/impact/`의 Markdown과 JSON을 읽습니다.
6. 표시된 `regenerate` 명령을 사용자에게 보여 줍니다. 자동으로 실행하지 않습니다.
7. 사용자가 갱신을 원하면 해당 스킬의 절차로 산출물을 다시 만들고, 새 manifest가 생겼는지 확인합니다.
8. 다시 stale 모드를 실행해 갱신 대상이 사라졌는지 확인합니다.

커밋 전 로컬 변경까지 보려면 `--working`을 붙입니다. CI에서는 `--head <PR head>`를 주고, manifest에 `generated_commit`이 없을 때만 `--base <merge-base>`를 fallback으로 넘깁니다. `--fail-on-stale`을 주면 갱신 대상이 있을 때 exit 1입니다.

### full 모드

1. 릴리스 후보, 큰 변경, 사용자 요청일 때만 `python3 <스킬 폴더>/scripts/change_impact.py --mode full`을 실행합니다.
2. `--base`를 생략하면 마지막 태그를 기준으로 잡습니다. 태그가 없으면 `origin/main` 또는 `main`과의 merge-base, 그것도 없으면 `HEAD~1`을 씁니다. 릴리스 범위가 다르면 `--base`로 직접 지정합니다. 이 값은 변경 분류 범위이며, stale 판정은 각 manifest의 최신 기준 commit(`generated_commit`과 manifest 마지막 커밋 중 최신)을 사용합니다.
3. 리포트의 변경 분류, 갱신 필요, 확인 제안을 읽습니다.
4. 갱신 대상은 `regenerate` 명령으로 다시 만들고, 테스트·API·DB 영향은 해당 스킬의 절차로 확인합니다.
5. 릴리스 점검은 `gorani-change-impact` → `gorani-release-check` → `gorani-release-note` 순서로 진행합니다.
6. `--fail-on-stale`을 주면 릴리스 전 갱신 누락을 CI에서 차단할 수 있습니다.

## 입력과 옵션

| 옵션 | 내용 |
| --- | --- |
| `--mode stale` | 기본값. manifest와 git diff만 비교 |
| `--mode full` | 릴리스용. 변경 분류와 확인 제안까지 생성 |
| `--root` | 저장소 경로. 기본은 현재 디렉터리 |
| `--base` | manifest에 `generated_commit`이 없을 때 쓸 fallback ref. full 모드에서는 변경 분류 기준 |
| `--head` | 비교 끝 ref. 기본은 `HEAD` |
| `--working` | 커밋되지 않은 변경과 untracked 파일 포함 |
| `--manifest-glob` | manifest 탐색 글롭. 기본은 `**/*.artifact.json` |
| `--outdir` | 리포트 출력 디렉터리. 기본은 `.gorani/impact` |
| `--formats` | `md,json` 조합. 기본은 둘 다 |
| `--print` | Markdown을 stdout에도 출력 |
| `--force` | stale이 없어도 리포트 파일 생성 |
| `--fail-on-stale` | 갱신 대상이 있으면 exit 1 |
| `--fail-on-unknown` | manifest를 확인할 수 없으면 exit 1 |
| `--now` | 테스트용 기준 시각(ISO 8601) |

## CI와 PR

매 PR마다 full 분석을 돌리지 않습니다. 아래 경로가 바뀔 때만 path-filter로 stale 검사를 실행합니다.

- `db/migrations/**`, `migrations/**`, `**/schema.sql`
- `openapi/**`, `**/openapi*.yaml`, `**/openapi*.yml`, `**/openapi*.json`
- `src/app/**/page.*`, `src/pages/**`, `src/routes/**`
- `.env*`, `docker-compose*.yml`, `k8s/**`
- `package.json`, lockfile, `requirements*.txt`, `pyproject.toml`
- `docs/**/*.artifact.json`

GitHub Actions 예시는 `samples/change-impact/pr-impact.yml`에 있습니다.

- `fetch-depth: 0`으로 manifest의 `generated_commit`을 찾을 수 있게 합니다.
- `--base`는 manifest에 `generated_commit`이 없을 때만 쓰이는 fallback입니다. 얕은 clone에서도 동작하게 남겨 두지만, 정상 clone에서는 manifest commit이 우선합니다.
- 얕은 clone에서 manifest commit이 아예 없으면 fallback 범위로 비교하므로, PR에서 재생성한 산출물이 stale로 보일 수 있습니다. `fetch-depth: 0`을 권장합니다.
- 갱신 대상이 있을 때만 `.gorani/impact/*.md`가 생깁니다.
- PR 코멘트는 그 파일이 있을 때만 답니다. 없으면 조용히 끝냅니다.
- `full`은 PR job에 넣지 않습니다. 릴리스 job이나 수동 실행에 둡니다.
- 샘플 워크플로는 경고만 하고 PR을 차단하지 않습니다. 안정화 후 `--fail-on-stale`을 추가합니다.

## 출력 형식

### stale

갱신 대상이 있을 때만 아래 파일을 만듭니다.

- `.gorani/impact/impact-<head>-stale.md`
- `.gorani/impact/impact-<head>-stale.json`
- `--working`을 주면 파일명에 `-working`이 붙습니다.

Markdown:

- 모드, 비교 기준, HEAD, 기준 시각
- 변경 파일, 갱신 필요, 변경 없음, 확인 불가 집계
- `## 갱신 필요`: 산출물, 스킬, 매칭된 변경 파일, 재생성 명령
- `## 확인 불가`: manifest 오류
- `## 경고`: 읽지 못한 manifest, 잘못된 commit

JSON:

- `summary`: 변경 파일, stale, clean, unknown, warnings 집계
- `stale`: manifest, skill, artifact, base, matched, regenerate
- `clean`: 변경이 없는 manifest
- `unknown`: 확인하지 못한 manifest와 오류
- `warnings`: 전체 경고

### full

항상 리포트를 만듭니다.

- `.gorani/impact/impact-<head>-full.md`
- `.gorani/impact/impact-<head>-full.json`

Markdown:

- stale과 같은 집계
- `## 갱신 필요`
- `## 확인 불가`
- `## 변경 분류`: frontend, api, db, config, dependencies, tests
- `## 확인 제안`: 변경 분류에 맞는 스킬과 확인 사항
- `## 릴리스 절차`: change-impact → release-check → release-note
- `## 경고`

JSON에는 같은 내용과 `categories`, `suggestions`가 추가됩니다.

## 기존 스킬과 연결

| 스킬 | manifest 소스 | 연결 |
| --- | --- | --- |
| `gorani-site-structure` | 입력 JSON, `src/app/**`, `src/pages/**`, `src/routes/**` | 화면·메뉴 변경 시 구조도 갱신 |
| `gorani-table-spec` | `--ddl` 경로, `--sources` | DDL·마이그레이션 변경 시 명세 갱신 |
| `gorani-api-contract-diff` | 이전·새 OpenAPI 경로, `--sources` | API 스펙 변경 시 계약 비교 |
| `gorani-release-check` | 배포 범위 | full 리포트 확인 후 배포 전 점검 |
| `gorani-release-note` | 릴리스 범위 | 고객 공지 문구 작성 |
| `gorani-cve-scan` | lockfile·manifest | 의존성 변경 시 CVE 확인 |
| `gorani-license-notice` | lockfile·SBOM | 의존성 변경 시 고지 갱신 |

`gorani-change-impact`는 다른 스킬을 직접 실행하지 않습니다. 갱신 명령과 다음 스킬만 제안합니다.

## 실패 처리

- manifest가 없으면 경고만 하고 exit 0입니다. 리포트 파일을 만들지 않습니다.
- manifest JSON을 읽지 못하면 확인 불가로 표시하고 경고를 남깁니다.
- `sources`가 비어 있으면 확인 불가로 표시합니다. `--sources`로 보정하도록 안내합니다.
- `generated_commit`과 manifest 마지막 커밋을 모두 찾을 수 없으면 확인 불가로 표시합니다. 얕은 clone이면 `--base`를 넘기도록 안내합니다.
- `--base`를 직접 줬는데 ref가 없으면 추측하지 않고 exit 2로 중단합니다.
- git 저장소가 아니거나 `--head`를 찾지 못하면 exit 2로 중단합니다.
- 산출물 재생성이 실패하면 오류와 실행한 명령을 보고합니다. 산출물을 손으로 고치지 않습니다.
- 오래된 manifest와 실제 산출물이 다르면 manifest를 믿고, 산출물을 다시 만들어 manifest를 갱신합니다.
- `.gorani/impact/`를 커밋하지 않습니다.

## 도구 설치

- Python 3와 git만 필요합니다. 추가 Python 패키지는 설치하지 않습니다.
- git이 없으면 OS 패키지 관리자로 설치를 시도합니다. macOS는 `brew`, Debian·Ubuntu는 `apt-get`, Fedora는 `dnf`, Arch는 `pacman`, Windows는 `winget`·`choco`·`scoop`을 사용합니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 거부하면 설치하지 않고 git이 있는 환경에서 실행하도록 요청합니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 다운로드·실행을 금지합니다.
- 설치 후 `command -v git`과 `git --version`으로 확인합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 저장소 코드·문서를 설치 과정에서 외부로 보내지 않습니다.

## 금지

- 산출물을 자동으로 수정하거나 덮어쓰지 않습니다. 갱신 명령만 제안합니다.
- 매 PR마다 `full` 모드를 실행하지 않습니다.
- 갱신 대상이 없는데 리포트 파일이나 PR 코멘트를 만들지 않습니다.
- manifest가 없는 산출물을 추측해 stale로 판정하지 않습니다.
- 기준 commit을 찾지 못했는데 최신이라고 간주하지 않습니다. 확인 불가로 남깁니다.
- stale 모드에 코드 파싱이나 전체 저장소 분석을 넣지 않습니다.
- `.gorani/impact/`를 커밋하지 않습니다.
- 사용자 지시 없이 커밋·푸시·PR을 만들지 않습니다.

## 문제 보고

스킬이 예상과 다르게 실패하거나 개선점·아이디어·양식 제안이 보이면, 원인이 이 스킬·스크립트에 있는지 확인한 뒤 `gorani-report`로 GitHub 이슈를 만들지 사용자에게 먼저 묻습니다. 공개 이슈에는 고객 정보·시크릿·내부 URL을 넣지 않고, 사용자 확인 후 작성합니다.
