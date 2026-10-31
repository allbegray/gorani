# 사이트 구조도

- 사이트: Admin Console
- 기준 URL: https://admin.example.com
- 검사 시점: 2026-10-31 14:00 KST
- 수집 기준: 렌더링된 프론트 레이아웃 (샘플)
- 적용 기준: KRDS 디지털 정부서비스 UI/UX 가이드라인 (2025.8) + 전자정부 웹사이트 품질관리 지침
- 검사 역할: admin, owner, member
- 검사 화면 폭: desktop, mobile
- Depth 규칙: 최소 2Depth, 최대 3Depth (KRDS 메인 메뉴 기준), 현재 2Depth
- 화면: 15
- 활성/계획/폐기: 14 / 1 / 0
- API 매핑: 22
- API only: 2
- 검토 메모: 13

> 이 문서는 실제 프론트 레이아웃을 확인해 정리한 구조도입니다. API 목록은 화면 구조의 근거가 아니며, 화면별 연결과 API only 부록으로만 사용합니다.

## 사이트 구조

| No | 1Depth | 2Depth | 화면 ID | 화면명 | 부모 화면 | 노출 | URL 패턴 | 레이아웃 | 접근 역할 | 데스크톱 | 모바일 | 상태 | 스크린샷 경로 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 대시보드 | - | dashboard | 대시보드 | - | 전역 메뉴 | / | dashboard | 전체 | Y | Y | active | screens/dashboard.png |
| 2 | 사용자 | 사용자 목록 | users-list | 사용자 목록 | - | 전역 메뉴 | /users | list | admin, owner | Y | Y | active | screens/users-list.png |
| 3 | 사용자 | 사용자 목록 | users-detail | 사용자 상세 | 사용자 목록 | 상세 진입 | /users/[id] | detail | admin | Y | Y | active | screens/users-detail.png |
| 4 | 사용자 | 사용자 목록 | users-invite | 사용자 초대 | 사용자 목록 | 액션 | /users/invite | form | admin | Y | N | active | screens/users-invite.png |
| 5 | 프로젝트 | 프로젝트 목록 | projects-list | 프로젝트 목록 | - | 전역 메뉴 | /projects | list | 전체 | Y | Y | active | screens/projects-list.png |
| 6 | 프로젝트 | 프로젝트 목록 | projects-detail | 프로젝트 상세 | 프로젝트 목록 | 상세 진입 | /projects/[id] | detail | 전체 | Y | Y | active | screens/projects-detail.png |
| 7 | 프로젝트 | 프로젝트 목록 | projects-members | 프로젝트 멤버 | 프로젝트 상세 | 탭 | /projects/[id]/members | list | owner, admin | Y | N | active | screens/projects-members.png |
| 8 | 프로젝트 | 프로젝트 목록 | projects-settings | 프로젝트 설정 | 프로젝트 상세 | 탭 | /projects/[id]/settings | settings | owner | Y | N | active | screens/projects-settings.png |
| 9 | 결제 | 요금제 | billing-plans | 요금제 | - | 전역 메뉴 | /billing/plans | list | owner, admin | Y | Y | active | screens/billing-plans.png |
| 10 | 결제 | 결제 수단 | billing-payment | 결제 수단 | - | 전역 메뉴 | /billing/payment-methods | settings | owner | Y | N | active | screens/billing-payment.png |
| 11 | 결제 | 결제 내역 | billing-invoices | 결제 내역 | - | 전역 메뉴 | /billing/invoices | list | owner, admin | Y | Y | active | screens/billing-invoices.png |
| 12 | 설정 | 프로필 | settings-profile | 프로필 | - | 전역 메뉴 | /settings/profile | form | 전체 | Y | Y | active | screens/settings-profile.png |
| 13 | 설정 | 알림 | settings-notifications | 알림 | - | 전역 메뉴 | /settings/notifications | settings | 전체 | Y | Y | active | screens/settings-notifications.png |
| 14 | 설정 | 보안 | settings-security | 보안 | - | 전역 메뉴 | /settings/security | settings | 전체 | Y | Y | active | screens/settings-security.png |
| 15 | 리포트 | 리포트 목록 | reports | 리포트 목록 | - | 전역 메뉴 | /reports | dashboard | admin | Y | N | planned | screens/reports.png |

## 화면 목록

| 화면 ID | 화면명 | 메뉴 경로 | URL 패턴 | 부모 화면 | 레이아웃 | 접근 역할 | 노출 방식 | 데스크톱 | 모바일 | 상태 | 스크린샷 경로 | API 호출 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dashboard | 대시보드 | 대시보드 | / | - | dashboard | 전체 | 전역 메뉴 | Y | Y | active | screens/dashboard.png | GET /api/dashboard/summary | - |
| users-list | 사용자 목록 | 사용자 > 사용자 목록 | /users | - | list | admin, owner | 전역 메뉴 | Y | Y | active | screens/users-list.png | GET /api/users | - |
| users-detail | 사용자 상세 | 사용자 > 사용자 목록 | /users/[id] | 사용자 목록 | detail | admin | 상세 진입 | Y | Y | active | screens/users-detail.png | GET /api/users/{id}<br>PATCH /api/users/{id} | 목록 행 클릭으로 진입 |
| users-invite | 사용자 초대 | 사용자 > 사용자 목록 | /users/invite | 사용자 목록 | form | admin | 액션 | Y | N | active | screens/users-invite.png | POST /api/users/invite | 목록 우측 상단 버튼 |
| projects-list | 프로젝트 목록 | 프로젝트 > 프로젝트 목록 | /projects | - | list | 전체 | 전역 메뉴 | Y | Y | active | screens/projects-list.png | GET /api/projects | - |
| projects-detail | 프로젝트 상세 | 프로젝트 > 프로젝트 목록 | /projects/[id] | 프로젝트 목록 | detail | 전체 | 상세 진입 | Y | Y | active | screens/projects-detail.png | GET /api/projects/{id} | 카드 클릭으로 진입 |
| projects-members | 프로젝트 멤버 | 프로젝트 > 프로젝트 목록 | /projects/[id]/members | 프로젝트 상세 | list | owner, admin | 탭 | Y | N | active | screens/projects-members.png | GET /api/projects/{id}/members<br>POST /api/projects/{id}/members<br>DELETE /api/projects/{id}/members/{userId} | 상세 화면 탭 |
| projects-settings | 프로젝트 설정 | 프로젝트 > 프로젝트 목록 | /projects/[id]/settings | 프로젝트 상세 | settings | owner | 탭 | Y | N | active | screens/projects-settings.png | PATCH /api/projects/{id} | owner만 노출 |
| billing-plans | 요금제 | 결제 > 요금제 | /billing/plans | - | list | owner, admin | 전역 메뉴 | Y | Y | active | screens/billing-plans.png | GET /api/billing/plans | - |
| billing-payment | 결제 수단 | 결제 > 결제 수단 | /billing/payment-methods | - | settings | owner | 전역 메뉴 | Y | N | active | screens/billing-payment.png | GET /api/billing/payment-methods<br>POST /api/billing/payment-methods | 모바일에서는 결제 메뉴 자체가 숨겨짐 |
| billing-invoices | 결제 내역 | 결제 > 결제 내역 | /billing/invoices | - | list | owner, admin | 전역 메뉴 | Y | Y | active | screens/billing-invoices.png | GET /api/billing/invoices | - |
| settings-profile | 프로필 | 설정 > 프로필 | /settings/profile | - | form | 전체 | 전역 메뉴 | Y | Y | active | screens/settings-profile.png | GET /api/me<br>PATCH /api/me | - |
| settings-notifications | 알림 | 설정 > 알림 | /settings/notifications | - | settings | 전체 | 전역 메뉴 | Y | Y | active | screens/settings-notifications.png | GET /api/me/notifications<br>PATCH /api/me/notifications | - |
| settings-security | 보안 | 설정 > 보안 | /settings/security | - | settings | 전체 | 전역 메뉴 | Y | Y | active | screens/settings-security.png | GET /api/me/sessions<br>POST /api/me/password | - |
| reports | 리포트 목록 | 리포트 > 리포트 목록 | /reports | - | dashboard | admin | 전역 메뉴 | Y | N | planned | screens/reports.png | GET /api/reports | 계획 상태, 실제 화면 미확인 |

## API 매핑

| 화면 ID | 화면명 | Method | API 경로 | 호출 시점 | 목적 |
| --- | --- | --- | --- | --- | --- |
| dashboard | 대시보드 | GET | /api/dashboard/summary | on load | 대시보드 요약 조회 |
| users-list | 사용자 목록 | GET | /api/users | on load | 사용자 목록 조회 |
| users-detail | 사용자 상세 | GET | /api/users/{id} | on load | 사용자 상세 조회 |
| users-detail | 사용자 상세 | PATCH | /api/users/{id} | 사용자 액션 | 사용자 정보 수정 |
| users-invite | 사용자 초대 | POST | /api/users/invite | 사용자 액션 | 사용자 초대 |
| projects-list | 프로젝트 목록 | GET | /api/projects | on load | 프로젝트 목록 조회 |
| projects-detail | 프로젝트 상세 | GET | /api/projects/{id} | on load | 프로젝트 상세 조회 |
| projects-members | 프로젝트 멤버 | GET | /api/projects/{id}/members | on load | 멤버 목록 조회 |
| projects-members | 프로젝트 멤버 | POST | /api/projects/{id}/members | 사용자 액션 | 멤버 추가 |
| projects-members | 프로젝트 멤버 | DELETE | /api/projects/{id}/members/{userId} | 사용자 액션 | 멤버 제거 |
| projects-settings | 프로젝트 설정 | PATCH | /api/projects/{id} | 사용자 액션 | 프로젝트 설정 수정 |
| billing-plans | 요금제 | GET | /api/billing/plans | on load | 요금제 조회 |
| billing-payment | 결제 수단 | GET | /api/billing/payment-methods | on load | 결제 수단 조회 |
| billing-payment | 결제 수단 | POST | /api/billing/payment-methods | 사용자 액션 | 결제 수단 추가 |
| billing-invoices | 결제 내역 | GET | /api/billing/invoices | on load | 결제 내역 조회 |
| settings-profile | 프로필 | GET | /api/me | on load | 내 정보 조회 |
| settings-profile | 프로필 | PATCH | /api/me | 사용자 액션 | 내 정보 수정 |
| settings-notifications | 알림 | GET | /api/me/notifications | on load | 알림 설정 조회 |
| settings-notifications | 알림 | PATCH | /api/me/notifications | 사용자 액션 | 알림 설정 수정 |
| settings-security | 보안 | GET | /api/me/sessions | on load | 세션 목록 조회 |
| settings-security | 보안 | POST | /api/me/password | 사용자 액션 | 비밀번호 변경 |
| reports | 리포트 목록 | GET | /api/reports | on load | 리포트 조회 (계획) |

## API only

| Method | API 경로 | 용도 | 호출 주체 | 화면 없음 사유 |
| --- | --- | --- | --- | --- |
| GET | /api/health | 서비스 상태 확인 | 인프라 모니터링 | 화면 없이 모니터링 도구가 호출 |
| POST | /api/webhooks/stripe | Stripe 결제 이벤트 수신 | Stripe webhook | 외부 시스템에서 호출 |

## 표준 근거

| 구분 | 문서 | 적용 항목 | 내용 | 링크 |
| --- | --- | --- | --- | --- |
| KRDS | [디지털 정부서비스 UI/UX 가이드라인 (2025.8)](https://www.krds.go.kr/html/site/component/component_03_02.html) | 메인 메뉴 | 서비스 정보 구조를 반영하고 메인 메뉴는 최대 3수준까지 사용 | https://www.krds.go.kr/html/site/component/component_03_02.html |
| KRDS | [디지털 정부서비스 UI/UX 가이드라인 (2025.8)](https://www.krds.go.kr/html/site/component/component_03_02.html) | 현재 위치 | 현재 페이지가 사이트 구조상 어디인지 활성 메뉴로 명확히 표시 | https://www.krds.go.kr/html/site/component/component_03_02.html |
| KRDS | [디지털 정부서비스 UI/UX 가이드라인 (2025.8)](https://www.krds.go.kr/html/site/utility/utility_07.html) | 레이아웃 | IA가 많고 depth가 깊은 화면은 LNB·SNB 사용 | https://www.krds.go.kr/html/site/utility/utility_07.html |
| KRDS | [디지털 정부서비스 UI/UX 가이드라인 (2025.8)](https://www.krds.go.kr/html/site/component/component_03_02.html) | 모바일 | 햄버거 메뉴·사이드 탭·집중 탐색 레이어 등 별도 패턴 사용 | https://www.krds.go.kr/html/site/component/component_03_02.html |
| KRDS | [디지털 정부서비스 UI/UX 가이드라인 (2025.8)](https://www.krds.go.kr/html/site/component/component_03_02.html) | 접근성 | KWCAG 2.2 기준 키보드 탐색, 메뉴 계층 구조, aria-current 제공 | https://www.krds.go.kr/html/site/component/component_03_02.html |
| 전자정부 | [전자정부 웹사이트 품질관리 지침 (2025.6.25.)](https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000260906&chrClsCd=010201) | 품질관리 | 공공 웹사이트 품질 기준과 준수 항목 확인 | https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000260906&chrClsCd=010201 |

## 검토 메모

| No | 구분 | 내용 | 확인 필요 |
| --- | --- | --- | --- |
| 1 | 레이아웃 | 사용자 상세·초대는 전역 메뉴가 아니라 사용자 목록에서 진입한다. | 목록 화면의 행 클릭·초대 버튼 확인 |
| 2 | 레이아웃 | 모바일에서는 결제 메뉴가 숨겨지고 결제 수단 화면도 노출되지 않는다. | 모바일 내비게이션 확인 |
| 3 | 권한 | 프로젝트 설정은 owner에게만 노출된다. | owner/admin/member 역할별 확인 |
| 4 | API | API only 2건은 화면 구조도에 넣지 않고 별도 시트에 분리했다. | API only 시트 확인 |
| 5 | 상태 | 리포트 화면은 planned 상태이며 실제 캡처가 없다. | 기획 확정 후 재수집 |
| 6 | 증적 | 스크린샷은 엑셀에 삽입하지 않고 screens/ 아래 파일 경로만 기록한다. | 실제 수집 시 PNG 파일 저장 |
| 7 | 수집 방식 | Playwright는 선택 사항으로 두고, 권한·소요 시간 때문에 에이전트가 실제 화면을 먼저 확인한다. | 자동 수집이 필요한 경우 별도 옵션 |
| 8 | 구조 | Depth 컬럼은 실제 메뉴 계층만 표시하고, 상세·탭·액션 화면은 부모 화면으로 연결한다. | 사이트 구조 시트 확인 |
| 9 | Depth | 1~2Depth는 항상 유지하고, 실제 메뉴가 더 깊으면 프론트 소스·레이아웃 분석으로 컬럼을 추가한다. | 실제 수집 후 Depth 컬럼 수 확인 |
| 10 | KRDS | 메인 메뉴는 서비스 정보 구조를 반영하고 최대 3수준까지 사용한다. 현재 샘플은 2수준이다. | 3Depth 메뉴가 필요하면 컬럼 추가 |
| 11 | KRDS | 현재 페이지는 활성 메뉴로 명확히 표시하고, 모바일은 별도 메뉴 패턴을 확인한다. | 활성 메뉴·모바일 메뉴 확인 |
| 12 | 접근성 | KWCAG 2.2 기준 키보드 탐색·계층 구조·aria-current를 확인한다. | 메뉴 접근성 확인 |
| 13 | 품질관리 | 전자정부 웹사이트 품질관리 지침의 품질 기준을 확인한다. | KRDS·품질관리 지침 |

## 검토 요청

1. 메뉴 depth가 실제 프론트 메뉴 구조와 일치하는가?
2. 상세·탭·액션 화면이 부모 화면으로 연결됐는가?
3. API only가 화면 구조도와 분리됐는가?
4. 스크린샷 경로가 실제 화면과 일치하는가?
5. KRDS 메인 메뉴 최대 3Depth 기준을 지켰는가?
