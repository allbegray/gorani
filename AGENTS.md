# AGENTS.md — 저장소 작업 지침

## 이 저장소
- 팀 MD 관리 룰북을 AI CLI 에 프롬프트로 주입하는 배포 체계
- 핵심 파일: PROMPT.md (룰북 = 제품), README.md (한줄 명령 가이드), .gitignore
- 공개 저장소 (allbegray/gorani) — 시크릿/내부 정보 절대 금지

## 룰북(PROMPT.md) 수정 시 필수 규칙
- 모든 문서·커밋 메시지는 한국어
- 인라인 표기만 — 코드 펜스(triple backtick) 사용 금지
- 기존 요구사항 보존: 6종 양식(3.1-3.6), H/M/L 라벨, BACKLOG 완료 항목 [x] 표시 후 삭제(3.2), UTF-8, SECURITY 인증 curl 규칙(3.5), graphify 규칙(1장/3.1, 갱신은 CLI 직접 실행·skill/에이전트 경유 금지), git push 전 6종 최신화(0장)
- 수정 후 반드시 검증: scratch repo 에서 opencode run "$(cat PROMPT.md)" 실행 → 6종 생성 + 양식 준수 확인 → evidence .omo/evidence/ 기록

## 명령
- 커밋: git commit -m "docs: ..." (한국어) → git push origin main
- raw URL: https://raw.githubusercontent.com/allbegray/gorani/main/PROMPT.md

## 주의
- .omo/, .codegraph/, graphify-out/ 커밋 금지
- README 명령 구조 불변 (opencode run positional / claude -p / codex exec / curl.exe + UTF-8 프리픽스)

## 실행 기록
- 2026-08-12: PROMPT.md 수정 — BACKLOG 완료 항목 삭제 규칙(3.2), graphify CLI 직접 실행 규칙(1장/3.1). scratch repo 검증 완료, evidence: .omo/evidence/2026-08-12-prompt-backlog-delete-graphify-cli.md
- 2026-08-13: PROMPT.md 수정 — git push 전 필수 문서 6종 최신화 규칙(0장). scratch repo 검증 완료, evidence: .omo/evidence/2026-08-13-prompt-push-doc-update.md
