# Gorani

팀의 문서 관리 룰북(`PROMPT.md`)을 AI CLI(코딩 에이전트)에 프롬프트로 주입하는 체계입니다. 한 줄 명령을 실행하면 에이전트가 룰북을 받아 프로젝트를 분석하고, 필수 문서 6종을 자동으로 생성·보강·유지합니다.

이 문서는 두 가지 역할을 합니다.

1. 프로젝트의 `README.md`(필수 문서 6종 중 하나)
2. AI CLI 설치 및 사용 가이드

## 사전 준비

1. 프로젝트를 clone 합니다.

이 저장소는 공개 저장소이므로 별도 토큰 없이 raw URL에서 `PROMPT.md`를 내려받을 수 있습니다.

## 한 줄 명령

아래 명령은 raw URL에서 `PROMPT.md`(룰북)를 내려받아 AI CLI에 프롬프트로 전달합니다.

### PowerShell UTF-8 프리픽스

PowerShell은 한글 인코딩 안전을 위해 모든 명령 앞에 아래 프리픽스를 붙입니다. `irm` 대신 `curl.exe`를 사용합니다(UTF-8 디코딩 보장).

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
```

### opencode

PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md); opencode run "$p"
```

bash:

```bash
opencode run "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md)"
```

`opencode run`은 프롬프트를 위치 인자(positional message)로 받습니다. `-p`는 password 플래그이므로 사용하지 마세요.

### Claude Code

PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md); claude -p "$p"
```

bash:

```bash
claude -p "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md)"
```

`claude -p`(print 모드)는 비대화형 실행입니다.

### Codex

PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md); codex exec "$p"
```

bash:

```bash
codex exec "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md)"
```

`codex exec`는 Codex의 비대화형 실행 모드입니다.

### 기타 AI CLI

각 CLI의 공식 문서에서 비대화형(non-interactive) 모드 패턴을 확인하고, 같은 `FETCH` 구조를 프롬프트 인자로 전달하세요. 프롬프트를 인자로 받지 않는 CLI는 표준 입력(stdin) 파이프(`echo "$FETCH" | <cli>`)를 지원하는지 확인합니다.

## 동작 방식

프롬프트 주입 후 에이전트는 룰북(`PROMPT.md`) 지침에 따라 다음을 수행합니다.

- 필수 문서 6종(`AGENTS.md`, `BACKLOG.md`, `CHANGELOG.md`, `README.md`, `SECURITY.md`, `SOLUTION.md`)이 프로젝트 루트에 존재하는지 확인하고, 누락된 문서는 프로젝트 분석 후 즉시 생성
- 루트의 6종 외 `.md` 파일은 `docs/` 디렉터리로 이동
- 이후 코드 수정·디버깅 시 문서 자동 갱신
  - `AGENTS.md`: 실행 기록·개발 규칙 실시간 누적
  - `BACKLOG.md`: 할 일을 H/M/L 우선순위로 분류하고 `H1`/`M1`/`L1` 라벨 부여
  - `CHANGELOG.md`: 변경 사항을 한국어로 정리하고 시맨틱 버저닝(`MAJOR.MINOR.PATCH`)으로 버전 갱신
  - `SOLUTION.md`: 트러블슈팅 지식 통합 기록
- 모든 문서는 한국어로 작성

## 재실행

룰북을 다시 주입하면 에이전트가 6종 문서를 점검하고 정렬·보강합니다. 주기적으로 재실행하면 문서가 최신 상태로 유지됩니다.

## 신규·기존 프로젝트 공통

설치 절차는 동일합니다. 새 프로젝트든 기존 프로젝트든 clone 후 위 명령을 실행하면 6종 문서가 자동으로 정리됩니다.

## 자주 묻는 질문

### `PROMPT.md`가 `docs/`로 이동됐어요

정상입니다. 에이전트가 룰북의 거버넌스 규칙에 따라 루트의 6종 외 `.md` 파일을 `docs/`로 옮긴 것입니다. 명령은 매번 raw URL에서 `PROMPT.md`를 다시 받아오므로, 이동 후에도 다음 실행은 정상 동작합니다.

### 명령이 파일 쓰기 권한 프롬프트에서 멈춰요

opencode는 `--auto` 플래그로 권한을 자동 승인할 수 있습니다. 단, `--auto`는 명시적으로 거부되지 않은 모든 권한을 자동 승인하므로 **위험합니다**. 신뢰하는 환경에서만 사용하세요.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md); opencode run --auto "$p"
```

대안으로 opencode 설정에서 파일 쓰기 권한을 미리 허용하거나, 권한 프롬프트에서 수동 승인하면 됩니다. 다른 CLI도 비슷한 자동 승인 옵션(`--yes` 등)을 제공하는지 공식 문서를 확인하세요.
