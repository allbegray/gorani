# 릴리스 노트 검토 기록

이 파일은 내부 검토용입니다. 고객에게 배포하지 않습니다.

- 제품: SampleApp
- 버전: 2.0.0
- 배포일: 2026-10-27
- 대상: 앱 사용자
- 언어: ko
- commit: 8 (포함 5, 제외 3)
- 섹션 항목: 4
- 글자 수 제한: short 500, store 4000

- 비교 범위: v1.0.0..HEAD

## Commit 매핑

| Hash | 날짜 | 제목 | 분류 | 포함 | 비고 |
| --- | --- | --- | --- | --- | --- |
| a1b2c3d | 2026-10-20 | feat(search): add fuzzy search | feature | 예 | 새 기능 > 오타에도 강한 검색 |
| b2c3d4e | 2026-10-21 | fix(auth): handle expired token | fix | 예 | 수정 > 로그인이 풀리던 문제 |
| c3d4e5f | 2026-10-22 | perf: reduce startup time | improvement | 예 | 개선 > 앱 시작 속도 개선 |
| d4e5f60 | 2026-10-23 | chore: bump dependencies | internal | 아니오 | 의존성 업데이트, 고객에게 보이는 변화 없음 |
| e5f6071 | 2026-10-24 | feat!: remove legacy export | feature | 예 | 업그레이드 전 확인 > 레거시 내보내기 기능 종료 |
| f607182 | 2026-10-25 | security: patch XSS in preview | security | 예 | 보안 > 미리보기 화면 보안 강화 |
| a7b8c9d | 2026-10-26 | docs: update README | internal | 아니오 | README 문서 변경 |
| b8c9d0e | 2026-10-27 | Update stuff | other | 아니오 | 사용자에게 보이는 변화가 없어 제외 |

## 배포 전 확인

- 고객 문장의 모든 주장이 commit 또는 diff로 확인됐는가
- commit hash, 이슈 번호, 직원 이름, 내부 URL이 고객 문구에 없는가
- 업그레이드 전 확인 항목에 구체적인 조치가 있는가
- 링크가 https 또는 mailto이고 실제로 열리는가
- short/store 요약이 글자 수 제한 안에 있는가
- 지원 경로가 고객에게 보이는가
