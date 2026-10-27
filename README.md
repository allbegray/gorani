# Gorani

AI CLI(opencode, Claude Code, Codex)에 한 줄로 주입하는 프롬프트 모음집입니다. 프롬프트 파일 하나가 완결된 지시문이라, raw URL에서 내려받아 그대로 실행하면 됩니다.

## 프롬프트 목록

| 파일 | 하는 일 |
| --- | --- |
| `prompts/docs-governance.md` | 대상 프로젝트에 필수 문서 6종(AGENTS/BACKLOG/CHANGELOG/README/SECURITY/SOLUTION)을 생성하고 변경에 맞춰 유지 |

`prompts/` 아래 파일은 모두 플랫 구조이며, 각 파일은 다른 프롬프트를 참조하지 않고 단독으로 동작합니다.

### docs-governance가 하는 일

- 필수 문서 6종이 루트에 있는지 확인하고, 누락분은 프로젝트 분석 후 즉시 생성
- 루트의 6종 외 `.md` 파일은 `docs/`로 이동
- 코드 수정·디버깅 시 6종 문서 자동 갱신
  - `AGENTS.md`: 실행 기록·개발 규칙 실시간 누적
  - `BACKLOG.md`: 할 일을 H/M/L 우선순위로 분류하고 `H1`/`M1`/`L1` 라벨 부여, 완료 시 `[x]` 표시 후 항목 삭제
  - `CHANGELOG.md`: 변경 사항을 한국어로 정리하고 시맨틱 버저닝(`MAJOR.MINOR.PATCH`)으로 버전 갱신
  - `SOLUTION.md`: 트러블슈팅 지식 통합 기록
- git push 전 필수 문서 6종 최신화 확인
- 모든 문서는 한국어로 작성

## 사용법

### 사전 준비

이 저장소는 공개 저장소이므로 별도 토큰 없이 raw URL에서 프롬프트를 내려받을 수 있습니다.

### PowerShell UTF-8 프리픽스

PowerShell은 한글 인코딩 안전을 위해 모든 명령 앞에 아래 프리픽스를 붙입니다. `irm` 대신 `curl.exe`를 사용합니다(UTF-8 디코딩 보장).

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;
```

아래 예시는 `docs-governance.md`를 실행합니다. 프롬프트가 늘어나면 URL의 파일명만 바꿉니다.

### opencode

PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md); opencode run "$p"
```

bash:

```bash
opencode run "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md)"
```

`opencode run`은 프롬프트를 위치 인자(positional message)로 받습니다. `-p`는 password 플래그이므로 사용하지 마세요.

### Claude Code

PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md); claude -p "$p"
```

bash:

```bash
claude -p "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md)"
```

`claude -p`(print 모드)는 비대화형 실행입니다.

### Codex

PowerShell:

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md); codex exec "$p"
```

bash:

```bash
codex exec "$(curl -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md)"
```

`codex exec`는 Codex의 비대화형 실행 모드입니다.

### 기타 AI CLI

각 CLI의 공식 문서에서 비대화형(non-interactive) 모드 패턴을 확인하고, 같은 `FETCH` 구조를 프롬프트 인자로 전달하세요. 프롬프트를 인자로 받지 않는 CLI는 표준 입력(stdin) 파이프(`echo "$FETCH" | <cli>`)를 지원하는지 확인합니다.

## 프롬프트 추가하기

새 프롬프트는 `prompts/` 아래에 kebab-case `.md`로 추가하고 이 README의 목록에 한 줄 등록합니다. 형식은 다음을 따릅니다.

- H1 제목 + 역할 1줄
- `## 전제`(또는 `## 대상`), `## 절차`, `## 출력 형식`, `## 금지` 섹션
- 다른 프롬프트나 저장소 밖 파일을 참조하지 않는 자체 완결 지시문
- 한국어, 코드 펜스 없는 인라인 표기

## 재실행

같은 프롬프트를 다시 주입하면 에이전트가 결과물을 점검하고 정렬·보강합니다. 주기적으로 재실행하면 문서와 리뷰 결과가 최신 상태로 유지됩니다.

## 자주 묻는 질문

### 주입한 프롬프트 파일이 `docs/`로 이동됐어요

정상입니다. docs-governance 프롬프트가 루트의 6종 외 `.md` 파일을 `docs/`로 옮긴 것입니다. 명령은 매번 raw URL에서 프롬프트를 다시 받아오므로, 이동 후에도 다음 실행은 정상 동작합니다.

### 명령이 파일 쓰기 권한 프롬프트에서 멈춰요

opencode는 `--auto` 플래그로 권한을 자동 승인할 수 있습니다. 단, `--auto`는 명시적으로 거부되지 않은 모든 권한을 자동 승인하므로 **위험합니다**. 신뢰하는 환경에서만 사용하세요.

```powershell
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; $p=$(curl.exe -fsSL https://raw.githubusercontent.com/allbegray/gorani/main/prompts/docs-governance.md); opencode run --auto "$p"
```

대안으로 opencode 설정에서 파일 쓰기 권한을 미리 허용하거나, 권한 프롬프트에서 수동 승인하면 됩니다. 다른 CLI도 비슷한 자동 승인 옵션(`--yes` 등)을 제공하는지 공식 문서를 확인하세요.
