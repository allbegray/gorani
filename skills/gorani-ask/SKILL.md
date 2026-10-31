---
name: gorani-ask
description: 여러 gorani 스킬 중 지금 상황에 맞는 스킬과 작업 순서를 안내한다. 어떤 스킬을 써야 할지 모르거나 릴리스·API·DB·기획서·문서 작업을 어디서 시작할지 물을 때 사용.
metadata:
  version: "3.17.0"
  updated: "2026-10-31"
---

# Gorani Ask

스킬을 바로 실행하지 않고, 지금 상황에 맞는 **첫 스킬과 이어질 순서**를 고릅니다. 스킬이 많아도 이름을 외우지 않고 작업을 시작할 수 있게 하는 라우터입니다.

## 전제

- 아래 스킬 목록은 이 저장소의 현재 스킬과 같아야 합니다.
- 추천한 스킬의 내용을 설명할 때는 반드시 해당 `SKILL.md`를 읽고 확인합니다. 이름만 보고 추측하지 않습니다.
- 사용자가 추천만 원하면 추천에서 멈춥니다. 진행을 원하면 추천한 스킬의 절차를 따릅니다.
- 한 번에 여러 스킬을 실행하지 않습니다. 첫 스킬을 정하고, 끝난 뒤 다음 스킬로 넘어갑니다.
- 맞는 스킬이 없으면 억지로 고르지 않고 “맞는 gorani 스킬 없음”이라고 말합니다.

## 스킬 지도

| 스킬 | 이럴 때 | 결과 |
| --- | --- | --- |
| `gorani-docs-governance` | README·LICENSE·CONTRIBUTING·SECURITY·CHANGELOG·이슈/PR 템플릿을 정리할 때 | 루트 6종 + `.github` 5종 |
| `gorani-spec-analysis` | 기획서·요구사항을 읽고 용어·도메인·프로세스·플로우를 정리할 때 | 분석 문서 패키지 |
| `gorani-site-structure` | 실제 프론트 메뉴·탭·레이아웃을 사이트 구조도로 만들 때 | Excel·Markdown·HTML 구조도 |
| `gorani-api-contract-diff` | OpenAPI 이전·새 스펙의 breaking change를 볼 때 | API별 변경 리포트 |
| `gorani-table-spec` | DDL 또는 실제 DB에서 테이블 명세서를 만들 때 | Excel·Markdown·HTML 명세서 |
| `gorani-release-check` | 배포 전 브랜치·리비전 diff를 점검할 때 | P0~P4 점검 엑셀 |
| `gorani-cve-scan` | 의존성 CVE·SBOM·VEX를 확인할 때 | CVE 요약·조치 목록 |
| `gorani-dependency-update` | 의존성을 최신 안정·CVE 최소 수정으로 올릴 때 | 업데이트 계획·적용·검증 |
| `gorani-license-notice` | 앱·백엔드에 오픈소스 고지 페이지를 넣을 때 | 고지 HTML·md·검토 목록 |
| `gorani-release-note` | 고객용 릴리스 노트·스토어 업데이트 문구를 쓸 때 | HTML·md·스토어 요약 |
| `gorani-change-impact` | 기존 산출물이 소스 변경으로 낡았는지 확인할 때 | 갱신 필요 산출물·재생성 명령 |
| `gorani-report` | 스킬 오류·개선·아이디어·양식 제안을 GitHub 이슈로 남기고 싶을 때 | 마스킹된 이슈 드래프트·생성 URL |
| `gorani-ask` | 어떤 스킬을 써야 할지 모를 때 | 추천 스킬과 작업 순서 |

## 먼저 확인할 것

사용자 말에서 아래 세 가지를 찾습니다. 이미 있으면 다시 묻지 않습니다.

1. **결과물**: 문서, 엑셀, HTML, 리포트, 코드 변경, 배포 판단, GitHub 이슈 중 무엇인가?
2. **가진 자료**: 기획서, OpenAPI, DDL/DB, git 브랜치·태그, 프론트 URL, SBOM, 없음
3. **단계**: 기획, 변경, 배포 전, 배포 후, 문서 정리

세 가지가 모두 애매하면 한 번에 하나씩 묻습니다.

- “지금 만들려는 결과물은 무엇인가요?”
- “이미 가지고 있는 자료는 무엇인가요?”
- “배포 전 점검인가요, 문서 정리인가요?”

## 추천 절차

1. 사용자 말에서 상황을 분류합니다.
2. 가장 가까운 **첫 스킬 하나**를 고릅니다.
3. 필요한 입력이 없으면 추천과 함께 준비물을 알려 줍니다.
4. 이어서 할 스킬이 있으면 순서만 제안합니다.
5. 사용자가 진행을 원하면 해당 스킬의 `SKILL.md`를 읽고 그 절차를 따릅니다.

## 주요 작업 경로

### 릴리스 전체

`gorani-change-impact` → `gorani-release-check` → `gorani-cve-scan` → `gorani-license-notice` → `gorani-release-note`

- 먼저 갱신이 필요한 기존 산출물이 있는지 확인합니다.
- 이어서 배포 diff와 점검 항목을 봅니다.
- 의존성 CVE와 고지 의무를 확인합니다.
- 마지막에 고객에게 나갈 문구를 만듭니다.

### 문제 보고

`gorani-report`

- 스킬이 실패했거나 개선·아이디어·양식 제안이 보이면 명령·오류 로그·제안 내용·환경을 모아 드래프트를 만듭니다.
- 공개 이슈 작성 전 사용자 확인을 받고, 중복 이슈가 있으면 코멘트를 먼저 제안합니다.
- `gh`가 없거나 인증되지 않았으면 드래프트만 남기고 `gh auth login`을 안내합니다.

### 산출물 갱신

`gorani-change-impact` → `gorani-site-structure`·`gorani-table-spec`·`gorani-api-contract-diff` 중 해당 스킬

- `stale` 모드로 갱신 대상과 매칭된 변경 파일을 확인합니다.
- 리포트의 `regenerate` 명령으로 산출물을 다시 만들고 manifest를 갱신합니다.
- `full` 모드는 릴리스 전이나 사용자가 요청할 때만 사용합니다.

### API 변경

`gorani-api-contract-diff` → `gorani-release-check` → `gorani-release-note`

- API 계약 변경과 클라이언트 영향을 먼저 봅니다.
- 배포 전 점검 항목으로 넘깁니다.
- 고객 공지가 필요하면 릴리스 노트를 만듭니다.

### DB 변경

`gorani-table-spec` → `gorani-release-check`

- DDL 또는 실제 DB에서 테이블 명세서를 만듭니다.
- 배포 전 데이터·마이그레이션 점검으로 넘깁니다.

### 기획서에서 화면 구조까지

`gorani-spec-analysis` → `gorani-site-structure` → `gorani-docs-governance`

- 기획서의 용어·도메인·프로세스를 정리합니다.
- 실제 프론트 레이아웃을 확인해 사이트 구조도를 만듭니다.
- 프로젝트 문서 체계를 정리합니다.

### 의존성·보안

`gorani-cve-scan` → `gorani-dependency-update` → `gorani-release-check`

- 먼저 취약점과 영향 범위를 봅니다.
- 수정 범위와 업데이트 모드를 정합니다.
- 배포 전 점검으로 넘깁니다.

### 문서만 정리

`gorani-docs-governance`

- README, LICENSE, CONTRIBUTING, SECURITY, CHANGELOG, 이슈/PR 템플릿을 정리합니다.

## 응답 형식

추천할 때는 아래 형식으로 짧게 답합니다.

- 추천: `gorani-...`
- 이유: ...
- 준비물: ...
- 다음 단계: ...
- 이어서: `gorani-...` (있을 때만)

예:

- 추천: `gorani-api-contract-diff`
- 이유: 이전·새 OpenAPI 스펙이 있고, breaking change와 클라이언트 영향을 먼저 봐야 합니다.
- 준비물: 이전 스펙, 새 스펙, 서비스명, 배포 버전, 영향 클라이언트
- 다음 단계: `--fail-on-breaking`으로 CI 차단 여부를 정한 뒤 `gorani-release-check`로 넘어갑니다.

## 하지 말 것

- 스킬 이름만 보고 내용을 설명하지 않습니다. 해당 `SKILL.md`를 읽고 확인합니다.
- 맞는 스킬이 없는데 가장 비슷한 스킬을 억지로 추천하지 않습니다.
- 사용자가 추천만 원했는데 산출물을 만들지 않습니다.
- 한 번에 여러 스킬을 실행하지 않습니다.
- 없는 입력을 추측해 채우지 않습니다.
- API나 URL만으로 사이트 구조를 만들지 않습니다. 사이트 구조는 `gorani-site-structure`의 실제 프론트 확인 절차를 따릅니다.

## 유지보수

스킬이 추가·이름 변경·삭제되거나 작업 경로가 바뀌면 이 파일의 **스킬 지도**와 **주요 작업 경로**를 같은 변경에 갱신합니다. `gorani-ask`가 오래된 스킬을 추천하면 라우터가 없는 것보다 더 위험합니다.

## 문제 보고

스킬이 예상과 다르게 실패하거나 개선점·아이디어·양식 제안이 보이면, 원인이 이 스킬·스크립트에 있는지 확인한 뒤 `gorani-report`로 GitHub 이슈를 만들지 사용자에게 먼저 묻습니다. 공개 이슈에는 고객 정보·시크릿·내부 URL을 넣지 않고, 사용자 확인 후 작성합니다.
