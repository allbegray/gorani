# Gorani

AI CLI에 붙여 쓰는 실무 스킬 모음입니다. 스킬은 Agent Skills 표준(`SKILL.md`)을 따르므로 opencode와 Claude Code가 같은 파일을 읽습니다. 설치 없이 프롬프트로 넘길 수도 있습니다.

## 스킬

| 스킬 | 이럴 때 | 결과 |
| --- | --- | --- |
| `docs-governance` | 프로젝트 문서 체계를 처음 잡을 때, 코드 변경 후 문서를 맞출 때 | 루트 문서 6종 + `.github` 5종 |
| `cve-scan` | 의존성 취약점을 확인할 때, 릴리스 전 보안을 볼 때 | VEX 엑셀 + OpenVEX JSON, 조치 목록 |
| `release-check` | 운영 배포 전 운영·개발 브랜치 차이를 볼 때 | P0/P1/P2 점검 엑셀 |

## 각 스킬이 하는 일

### docs-governance

프로젝트를 먼저 읽고 실제 빌드·테스트 명령을 반영해 문서 11종을 만듭니다.

- 루트: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG
- `.github`: PULL_REQUEST_TEMPLATE, ISSUE_TEMPLATE 3종, CODEOWNERS

기존 문서는 지우지 않고 빠진 섹션만 채웁니다. LICENSE, 신고 연락처, CODEOWNERS 핸들은 확인 없이 만들지 않고, 비대화형 실행이면 "확인 필요"로 남깁니다.

### cve-scan

`syft`로 SBOM을 만들고 `grype`로 대조한 뒤 `osv-scanner`와 `trivy`로 교차 확인합니다. 대상은 소스 의존성이고 컨테이너 이미지는 다루지 않습니다.

- 같은 취약점은 하나로 합치고 높은 심각도를 채택
- 수정 버전이 있으면 `affected`, 없으면 `under_investigation`이 기본
- 결과: `docs/security/cve-report-YYYY-MM-DD.xlsx`와 같은 이름의 `.vex.json`
- 패키지를 올리지는 않고 조치 목록만 제시

### release-check

`main...develop`(merge-base 기준) diff에서 커밋과 변경 파일을 모아 점검 항목을 만듭니다.

- P0 배포 차단 / P1 주요 기능 / P2 경미
- QA가 확인할 항목과 개발자만 확인할 항목을 나누고, 개발자 항목은 시트 하단에 배치
- 결과: `docs/qa/release-check-YYYY-MM-DD.xlsx`
- 코드는 건드리지 않음

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
for s in docs-governance cve-scan release-check; do ln -s ~/gorani/skills/$s "$SCOPE/$s"; done
```

Claude Code — 같은 방식으로 위치만 바꿉니다.

```bash
SCOPE=.claude/skills          # 프로젝트에만
# SCOPE=~/.claude/skills      # 모든 프로젝트

mkdir -p "$SCOPE"
for s in docs-governance cve-scan release-check; do ln -s ~/gorani/skills/$s "$SCOPE/$s"; done
```

opencode는 Claude 호환 경로(`.claude/skills`, `~/.claude/skills`)도 읽으므로, Claude Code 위치에 한 번만 설치해도 둘 다 사용할 수 있습니다. 설치 후 에이전트를 실행하면 스킬 목록에 세 스킬이 보입니다.

## 프롬프트로 쓰기

저장소를 설치하지 않고 raw URL에서 `SKILL.md`를 받아 프롬프트로 넘깁니다. 아래 예시의 `S` 값만 바꾸면 다른 스킬을 실행합니다.

PowerShell은 한글 인코딩을 위해 아래 프리픽스를 붙이고 `irm` 대신 `curl.exe`를 씁니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
```

opencode — 프롬프트는 위치 인자로 넘깁니다. `-p`는 password 플래그라 쓰지 않습니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); opencode run "$p"
```

```bash
S=docs-governance
opencode run "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md)"
```

Claude Code — `-p`는 print(비대화형) 모드입니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); claude -p "$p"
```

```bash
S=docs-governance
claude -p "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md)"
```

Codex — 비대화형 실행은 `exec`입니다.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); codex exec "$p"
```

```bash
S=docs-governance
codex exec "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md)"
```

다른 CLI는 공식 문서에서 비대화형 모드를 확인하세요. 프롬프트를 인자로 받지 않으면 stdin 파이프(`echo "$p" | <cli>`)를 씁니다.

opencode에서 권한 프롬프트를 매번 승인하기 번거로우면 `--auto`를 쓸 수 있습니다. 명시적으로 거부하지 않은 모든 권한을 자동 승인하므로 신뢰하는 환경에서만 사용하세요.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $S="docs-governance"; $p=$(curl.exe -fsSL "https://raw.githubusercontent.com/allbegray/gorani/main/skills/$S/SKILL.md"); opencode run --auto "$p"
```

## 결과물 예시

`samples/`에 입력 JSON과 생성 결과를 함께 두었습니다. 같은 입력으로 다시 만들 수 있습니다.

| 파일 | 내용 |
| --- | --- |
| `samples/cve-scan/cve-report-sample.xlsx` | VEX 엑셀 (요약, VEX 판정, 원본 findings, 실행 로그) |
| `samples/cve-scan/cve-report-sample.vex.json` | OpenVEX JSON |
| `samples/release-check/release-check-sample.xlsx` | 릴리스 점검 엑셀 (요약, 점검 항목, 변경 파일, 커밋, 실행 로그) |

샘플 데이터는 형식 설명용 가상 데이터입니다. 재생성 명령은 `samples/README.md`에 있습니다.

## 스킬 추가

1. `skills/<이름>/SKILL.md`를 만듭니다. frontmatter의 `name`은 폴더명과 같게, `description`은 언제 쓰는지를 앞세워 1-1024자로 씁니다.
2. 본문은 H1 + 역할 한 줄로 시작하고 `## 전제`, `## 절차`, `## 출력`, `## 금지` 같은 섹션을 둡니다.
3. 한국어로 쓰고, 코드 펜스 없이 인라인으로 표기하며, 다른 스킬이나 저장소 밖 파일을 참조하지 않습니다.
4. 보조 스크립트가 필요하면 `skills/<이름>/scripts/`에 둡니다.
5. 위 스킬 표에 한 줄 추가합니다.

## 저장소 구조

```
skills/<이름>/SKILL.md      스킬 본문
skills/<이름>/scripts/      스킬 전용 스크립트
samples/<스킬>/             예시 입력과 결과물
```

## 문제 해결

| 증상 | 확인 |
| --- | --- |
| 스킬 목록에 안 보임 | `SKILL.md` 대문자 여부, frontmatter의 `name`이 폴더명과 같은지, 같은 이름의 스킬이 여러 위치에 있는지 |
| 루트 `.md`가 `docs/`로 이동함 | docs-governance가 문서 세트 외 `.md`를 옮긴 것. 스킬 폴더는 대상이 아님 |
| cve-scan이 도구가 없다고 함 | `brew install osv-scanner trivy syft grype` 후 재실행. 스킬은 도구를 임의 설치하지 않음 |
| VEX 엑셀 생성 실패 | `python3 -m pip install --user openpyxl` 필요. 설치 전에는 임의 설치하지 않음 |
| release-check가 브랜치를 못 찾음 | `git fetch origin` 후 `main`·`develop` 존재 확인. 다른 이름이면 스킬에 알려줄 것 |
