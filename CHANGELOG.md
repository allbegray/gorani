# 변경 이력

## [v0.2.0] - 2026-08-12

### 추가
- graphify 초기 빌드·갱신 시 CLI 명령 직접 실행 규칙 (skill/에이전트 경유 금지, 빠른 동작 보장)

### 변경
- BACKLOG.md 완료 항목 처리: [x] 표시 후 즉시 삭제 (기존: [x] 표시 유지·삭제 금지)

## [v0.1.0] - 2026-08-08

### 추가
- AI CLI(opencode/claude/codex/기타)에 룰북을 프롬프트로 주입하는 한줄 명령 체계 (PowerShell + bash)
- 필수 문서 6종(AGENTS/BACKLOG/CHANGELOG/README/SECURITY/SOLUTION.md) 자동 생성·관리 룰북
- 6종 파일별 필수 양식 명세 (룰북 3.1-3.6)
- SECURITY.md 인증(Basic/JWT/API Key) 방식 설명 + curl 예시 규칙 (자리표시자 필수)
- graphify 지식 그래프 설치·구축 및 코드 검색/수정 시 동기화 규칙
- 저장소 작업 지침 AGENTS.md

### 변경
- 저장소 이전: aimnext-dev1/ai-prompt → allbegray/gorani (공개 저장소 전환)
- 룰북 구조 최적화: 중복 규칙(6종 목록/누락 생성/AGENTS 유지/init-deep) 3회 반복 → 1회 (43줄)
- README 헤더를 Gorani 로 변경, GH_TOKEN 요구 제거 (공개 저장소)

### 수정
- PowerShell 한줄 명령 PS 5.1 호환: 인라인 $() 치환 → 변수 경유 패턴
