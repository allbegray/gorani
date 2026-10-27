---
name: docs-governance
description: GitHub 기본 문서 세트(README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG, 이슈/PR 템플릿, CODEOWNERS)를 생성·유지한다. 새 프로젝트의 문서 체계를 세팅하거나, 코드 변경 후 문서를 최신화하거나, push 전 문서 점검이 필요할 때 사용.
---

# GitHub 표준 문서 생성·유지

프로젝트를 분석해 GitHub가 인식하는 문서 파일을 같은 양식으로 생성하고, 코드 변경에 맞춰 최신 상태로 유지합니다.

## 문서 세트

루트:

- README.md — 프로젝트명과 한 줄 소개, 시작하기(설치·실행), 사용법, 주요 기능, 기여·라이선스 링크
- LICENSE — SPDX 식별자에 해당하는 전문, 저작권자, 연도
- CONTRIBUTING.md — 개발 환경 준비, 브랜치·커밋 규칙, PR 절차, 테스트·린트 명령
- CODE_OF_CONDUCT.md — Contributor Covenant 2.1 기준, 위반 신고 연락처
- SECURITY.md — 지원 버전, 취약점 비공개 보고 방법, 응답 기한, 비밀 관리 규칙
- CHANGELOG.md — Keep a Changelog 형식, 시맨틱 버저닝, 최신 버전이 최상단

.github:

- PULL_REQUEST_TEMPLATE.md — 변경 요약, 관련 이슈, 테스트 방법, 체크리스트
- ISSUE_TEMPLATE/bug_report.yml — 재현 절차, 기대·실제 동작, 환경, 로그
- ISSUE_TEMPLATE/feature_request.yml — 해결할 문제, 제안, 대안
- ISSUE_TEMPLATE/config.yml — 빈 이슈 허용 여부, 외부 링크
- CODEOWNERS — 경로별 소유자

## 생성 절차

1. 저장소 분석: 언어·프레임워크·빌드/테스트 명령·패키지 매니저·배포 방식·기존 문서 확인
2. 기존 문서 확인: 있으면 내용을 보존하고 누락 섹션만 보강. 삭제·전면 교체 금지
3. 누락 문서 생성: 위 양식에 맞춰 실제 프로젝트 정보로 작성
4. 위치 정리: 문서 세트 외 `.md` 는 `docs/` 로 이동. 루트에는 문서 세트만 남김
5. 검증: 11개 경로 존재, 필수 섹션 포함, 내부 링크 유효성 확인

## 확인이 필요한 값

- LICENSE: 프로젝트에 라이선스 정보가 없으면 임의로 선택하지 않고 후보와 영향을 설명한 뒤 질문
- CODE_OF_CONDUCT 연락처, SECURITY 보고 채널: 실제 값이 없으면 질문. 추측한 이메일·URL 사용 금지
- SECURITY 응답 기한, 브랜치·커밋 규칙처럼 저장소에 근거가 없는 정책 값: 임의로 정하지 말고 확인 필요로 보고
- CODEOWNERS: GitHub 사용자·팀 핸들을 확인. 확인되지 않으면 파일 생성 보류

## 비대화형 실행

질문할 수 없는 환경(CI, `opencode run`)이면 확인이 필요한 값을 임의로 채우지 않고, 생성한 문서와 "확인 필요" 목록을 함께 보고합니다. 사용자가 값을 미리 제공했으면 그 값으로 생성하고, 제공되지 않은 LICENSE, CODEOWNERS, SECURITY 신고 채널은 확인 전까지 만들지 않습니다.

## 작성 규칙

- 본문은 한국어 (고유명사·명령·경로는 원문 유지)
- 날짜는 실제 날짜(`YYYY-MM-DD`) 사용, 자리표시자 금지
- CHANGELOG 최초 생성 시 현재 프로젝트 버전을 확인해 그 버전과 실제 날짜 기록. 버전 정보가 없으면 `v0.1.0`
- 내부 링크는 상대 경로 사용
- 실제 토큰·비밀번호·내부 URL 기재 금지

## 업데이트 규칙

- 기능·사용법 변경 → README, CHANGELOG
- 의존성·빌드 명령 변경 → CONTRIBUTING, README
- 보안 정책·지원 버전 변경 → SECURITY
- 버전 릴리스 → CHANGELOG 새 버전 (`MAJOR.MINOR.PATCH`, 파괴적=MAJOR, 기능=MINOR, 수정=PATCH)
- push 전: 문서 세트가 코드와 어긋나지 않는지 확인

## 금지

- LICENSE 임의 선택, 저작권자 추측
- 기존 문서 삭제나 전체 덮어쓰기
- 확인되지 않은 연락처·핸들로 CODEOWNERS, SECURITY, CODE_OF_CONDUCT 작성
- 스캔하거나 확인하지 않은 내용을 문서에 단정적으로 기록
