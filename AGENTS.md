# AGENTS.md — 저장소 작업 지침

## 이 저장소
- AI CLI(opencode/Claude Code/Codex)에 주입하는 프롬프트 모음집
- 제품: prompts/ 아래 프롬프트 파일 (플랫 구조, 파일 1개 = 완결된 지시문)
- 보조 문서: README.md (프롬프트 목록·한줄 명령 가이드), CHANGELOG.md
- 공개 저장소 (allbegray/gorani) — 시크릿/내부 정보 절대 금지

## 프롬프트 작성 규칙
- 모든 문서·프롬프트·커밋 메시지는 한국어
- 인라인 표기만 — 코드 펜스(triple backtick) 사용 금지
- 다른 프롬프트·저장소 밖 파일을 참조하지 않는 자체 완결 지시문
- 파일명은 kebab-case `.md`, 구성은 H1 + 역할 1줄 + `## 전제`/`## 대상`/`## 절차`/`## 출력 형식`/`## 금지`
- 새 프롬프트 추가 시 README 프롬프트 목록에 한 줄 등록

## docs-governance 프롬프트(prompts/docs-governance.md) 수정 시 필수 규칙
- 기존 요구사항 보존: 6종 양식(3.1-3.6), H/M/L 라벨, BACKLOG 완료 항목 [x] 표시 후 삭제(3.2), UTF-8, SECURITY 인증 curl 규칙(3.5), graphify 규칙(1장/3.1, 갱신은 CLI 직접 실행·skill/에이전트 경유 금지), git push 전 6종 최신화(0장)
- 수정 후 반드시 검증: scratch repo 에서 opencode run "$(cat prompts/docs-governance.md)" 실행 → 6종 생성 + 양식 준수 확인 → evidence .omo/evidence/ 기록

## 명령
- 커밋: git commit -m "docs: ..." (한국어) → git push origin main
- raw URL: https://raw.githubusercontent.com/allbegray/gorani/main/prompts/<프롬프트>.md

## 주의
- .omo/, .codegraph/, graphify-out/ 커밋 금지
- README 명령 구조 불변 (opencode run positional / claude -p / codex exec / curl.exe + UTF-8 프리픽스)

## 실행 기록
- 2026-08-12: PROMPT.md 수정 — BACKLOG 완료 항목 삭제 규칙(3.2), graphify CLI 직접 실행 규칙(1장/3.1). scratch repo 검증 완료, evidence: .omo/evidence/2026-08-12-prompt-backlog-delete-graphify-cli.md
- 2026-08-13: PROMPT.md 수정 — git push 전 필수 문서 6종 최신화 규칙(0장). scratch repo 검증 완료, evidence: .omo/evidence/2026-08-13-prompt-push-doc-update.md
- 2026-10-27: 프롬프트 모음집으로 재편 — PROMPT.md → prompts/docs-governance.md 이동(내용 동일), README를 프롬프트 목록·추가 규칙 중심으로 재구성. evidence: .omo/evidence/2026-10-27-prompt-collection-restructure.md
