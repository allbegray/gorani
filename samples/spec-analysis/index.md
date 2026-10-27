# 장비 예약 서비스 분석

> 문서 지도: [index](index.md) · [source.plain](source.plain.md) · [source](source.md) · [glossary](glossary.md) · [domain](domain.md) · [processes](processes.md) · [flows](flows.md) · [validation](validation.md)

- 원본: `source.plain.md` (Markdown, 7개 섹션)
- 원문 보존: both (`source.plain.md` + `source.md`)
- ID·링크 수준: full
- 범위: 사내 장비 예약·승인·대여·반납의 1차 웹 출시
- 대상: 임직원, 운영자, 승인자, 관리자
- 준비 상태: **blocked**

## 한 줄 요약

장비 예약과 승인 흐름은 정의되어 있지만, 반납·연체·취소 정책과 승인자 권한이 비어 있어 예약 상태를 끝까지 닫을 수 없습니다.

## 핵심 발견

- blocker 2건: 반납 프로세스 미정의, 연체·노쇼 정책 미정의
- major 4건: 승인자 역할/SLA, 예약·대여 용어 충돌, 장비 상태·재고 정의, 취소·변경 정책
- question 3건: 외부 캘린더 실패 동작, 데이터 보존 기간, 승인 SLA·거절 사유

## 산출물

| 문서 | 내용 |
| --- | --- |
| `index.md` | 분석 범위·핵심 발견·ID Index·결정 필요 항목 |
| `source.plain.md` | 원본을 그대로 옮긴 단순 markdown |
| `source.md` | 추적용 변환 원문 (frontmatter·페이지 표시) |
| `glossary.md` | 용어 사전과 동의어·충돌 |
| `domain.md` | 도메인 모델과 상태 전이 |
| `processes.md` | 예약·승인·수령·반납 프로세스 |
| `flows.md` | 예약·승인 Mermaid 플로우차트 |
| `validation.md` | finding 10건과 추적성 |

## ID 규칙

ID는 `{TYPE}-{AREA}-{TOPIC}-{NN}` 형식입니다. 심각도는 ID에 넣지 않습니다.

| AREA | 의미 | V | P | F |
| --- | --- | --- | --- | --- |
| PROC | 프로세스 정의·예외 | 3 | 0 | 0 |
| STATUS | 상태·연체 | 1 | 0 | 0 |
| PERM | 역할·권한 | 1 | 0 | 0 |
| TERM | 용어 | 2 | 0 | 0 |
| DATA | 데이터 모델·재고·보존 | 2 | 0 | 0 |
| INT | 외부 캘린더 연동 | 1 | 0 | 0 |
| RESERVATION | 예약 업무 (이 문서에서 추가한 AREA) | 0 | 5 | 5 |

- 프로세스와 플로우는 같은 `AREA-TOPIC-NN`을 씁니다. 예: `P-RESERVATION-CREATE-01` / `F-RESERVATION-CREATE-01`.
- `RESERVATION`은 기본 카탈로그에 없어 이 문서의 `index.md`에서 먼저 정의한 프로젝트별 AREA입니다.
- 화면 ID가 원문에 없으므로 `S-` ID는 사용하지 않았습니다.
- `RESERVATION` F ID 5개 중 실제 도표는 3개입니다. 반납·취소는 프로세스만 정의되어 있습니다.

## Finding Index

| ID | 심각도 | 영역 | 요약 |
| --- | --- | --- | --- |
| [V-PROC-RETURN-01](validation.md#v-proc-return-01) | blocker | 프로세스·도메인 | 반납 프로세스 |
| [V-STATUS-OVERDUE-01](validation.md#v-status-overdue-01) | blocker | 정책 | 연체 정책 |
| [V-PERM-APPROVER-01](validation.md#v-perm-approver-01) | major | 역할 | 승인자 권한 |
| [V-TERM-RESERVATION-01](validation.md#v-term-reservation-01) | major | 용어·도메인 | 예약·대여 용어 |
| [V-DATA-INVENTORY-01](validation.md#v-data-inventory-01) | major | 데이터 | 수량·재고 |
| [V-PROC-CANCEL-01](validation.md#v-proc-cancel-01) | major | 정책 | 취소·변경 |
| [V-TERM-EQUIPMENT-01](validation.md#v-term-equipment-01) | minor | 용어 | 장비·자산 용어 |
| [V-INT-CALENDAR-01](validation.md#v-int-calendar-01) | question | 연동 | 캘린더 연동 |
| [V-DATA-RETENTION-01](validation.md#v-data-retention-01) | question | 데이터 | 보존 기간 |
| [V-PROC-APPROVAL-01](validation.md#v-proc-approval-01) | question | 프로세스 | 승인 SLA |

## Process Index

| ID | 이름 | 플로우 |
| --- | --- | --- |
| [P-RESERVATION-CREATE-01](processes.md#p-reservation-create-01) | 예약 신청 | [F-RESERVATION-CREATE-01](flows.md#f-reservation-create-01) |
| [P-RESERVATION-APPROVE-01](processes.md#p-reservation-approve-01) | 예약 승인 | [F-RESERVATION-APPROVE-01](flows.md#f-reservation-approve-01) |
| [P-RESERVATION-CHECKOUT-01](processes.md#p-reservation-checkout-01) | 장비 수령·대여 | [F-RESERVATION-CHECKOUT-01](flows.md#f-reservation-checkout-01) |
| [P-RESERVATION-RETURN-01](processes.md#p-reservation-return-01) | 반납 | [F-RESERVATION-RETURN-01](flows.md#f-reservation-return-01) |
| [P-RESERVATION-CANCEL-01](processes.md#p-reservation-cancel-01) | 취소·변경·노쇼 | [F-RESERVATION-CANCEL-01](flows.md#f-reservation-cancel-01) |

## Flow Index

| ID | 이름 | 프로세스 |
| --- | --- | --- |
| [F-RESERVATION-CREATE-01](flows.md#f-reservation-create-01) | 예약 신청 | [P-RESERVATION-CREATE-01](processes.md#p-reservation-create-01) |
| [F-RESERVATION-APPROVE-01](flows.md#f-reservation-approve-01) | 예약 승인 | [P-RESERVATION-APPROVE-01](processes.md#p-reservation-approve-01) |
| [F-RESERVATION-CHECKOUT-01](flows.md#f-reservation-checkout-01) | 장비 수령·대여 | [P-RESERVATION-CHECKOUT-01](processes.md#p-reservation-checkout-01) |
| [F-RESERVATION-RETURN-01](flows.md#f-reservation-return-01) | 반납 | [P-RESERVATION-RETURN-01](processes.md#p-reservation-return-01) |
| [F-RESERVATION-CANCEL-01](flows.md#f-reservation-cancel-01) | 취소·변경·노쇼 | [P-RESERVATION-CANCEL-01](processes.md#p-reservation-cancel-01) |

## 결정 필요

1. 반납과 연체를 어떤 상태·프로세스로 처리할 것인가
2. 승인자 역할과 승인 SLA를 어떻게 정의할 것인가
3. 예약 취소·변경·노쇼 정책을 1차 출시에 포함할 것인가
4. 외부 캘린더 연동 실패 시 예약 화면은 어떻게 동작해야 하는가
