# 검증 리포트

> 문서 지도: [index](index.md) · [source](source.md) · [glossary](glossary.md) · [domain](domain.md) · [processes](processes.md) · [flows](flows.md) · [validation](validation.md)

## 요약

| 심각도 | 건수 |
| --- | --- |
| blocker | 2 |
| major | 4 |
| minor | 1 |
| question | 3 |

준비 상태: **blocked**. 반납과 연체 정책이 없어 예약 상태를 닫을 수 없습니다.

## Findings

| ID | 심각도 | 영역 | 발견 내용 | 근거·출처 | 권장 조치 | 담당 | 상태 | 관련 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <a id="v-proc-return-01" name="v-proc-return-01"></a>V-PROC-RETURN-01 | blocker | 프로세스·도메인 | 반납 프로세스와 상태 전이가 정의되지 않음. "운영자가 처리한다"만 있음 | p.3, p.5 | 반납 단계, 확인 항목, 상태 전이, 파손·분실 처리를 정의 | 운영 | open | [P](processes.md#p-reservation-return-01) |
| <a id="v-status-overdue-01" name="v-status-overdue-01"></a>V-STATUS-OVERDUE-01 | blocker | 정책 | 연체를 정의만 하고 판정 기준·알림·제재가 없음 | p.3, p.5 | 연체 기준, 알림 시점, 제재·예외 정책 결정 | 운영 | open | [P](processes.md#p-reservation-return-01) |
| <a id="v-perm-approver-01" name="v-perm-approver-01"></a>V-PERM-APPROVER-01 | major | 역할 | 승인자 역할의 범위·권한·위임 규칙이 없음 | p.2 | 승인자 지정 방식, 운영자 겸임 여부, 권한 범위 정의 | 제품 | open | [P](processes.md#p-reservation-approve-01), [F](flows.md#f-reservation-approve-01) |
| <a id="v-term-reservation-01" name="v-term-reservation-01"></a>V-TERM-RESERVATION-01 | major | 용어·도메인 | 예약과 대여를 같은 뜻으로 쓰는 문장이 있어 상태 모델이 모호함 | p.2, p.3 | 예약=신청, 대여=수령 상태로 용어를 고정하고 문서 전체 수정 | 제품 | open | [P](processes.md#p-reservation-checkout-01), [F](flows.md#f-reservation-checkout-01) |
| <a id="v-data-inventory-01" name="v-data-inventory-01"></a>V-DATA-INVENTORY-01 | major | 데이터 | 예약 화면에는 수량이 있지만 예약 데이터 모델에는 수량이 없음. 장비 상태·재고 기준도 불명확 | p.4, p.5 | 수량 모델, 기간별 재고, 장비 상태 전이를 정의 | 개발 | open | [P](processes.md#p-reservation-create-01), [F](flows.md#f-reservation-create-01) |
| <a id="v-proc-cancel-01" name="v-proc-cancel-01"></a>V-PROC-CANCEL-01 | major | 정책 | 취소·변경·노쇼 정책이 없음 | p.3, p.5 | 1차 출시 포함 여부와 가능 시점·상태·페널티 결정 | 제품 | open | [P](processes.md#p-reservation-cancel-01) |
| <a id="v-term-equipment-01" name="v-term-equipment-01"></a>V-TERM-EQUIPMENT-01 | minor | 용어 | 장비와 자산을 같은 뜻으로 쓰지만 화면·API 이름이 정해지지 않음 | p.2 | `equipment`로 통일하고 화면·API·DB 매핑 표 추가 | 개발 | open | [P](processes.md#p-reservation-create-01) |
| <a id="v-int-calendar-01" name="v-int-calendar-01"></a>V-INT-CALENDAR-01 | question | 연동 | 외부 캘린더 연동 실패 시 예약 화면 동작이 없음 | p.4 | 실패 시 예약 차단·캐시·재시도 중 하나 결정 | 제품 | open | [P](processes.md#p-reservation-create-01) |
| <a id="v-data-retention-01" name="v-data-retention-01"></a>V-DATA-RETENTION-01 | question | 데이터 | 예약 데이터 보존 기간이 없음 | p.5 | 보존 기간과 파기·감사 로그 정책 결정 | 보안 | open | [P](processes.md#p-reservation-create-01) |
| <a id="v-proc-approval-01" name="v-proc-approval-01"></a>V-PROC-APPROVAL-01 | question | 프로세스 | 승인 SLA, 미응답 처리, 반려 사유 코드가 없음 | p.2, p.5 | SLA, 자동 처리, 사유 코드 결정 | 제품 | open | [P](processes.md#p-reservation-approve-01), [F](flows.md#f-reservation-approve-01) |

## 추적성

| 산출물 | 원문 근거 |
| --- | --- |
| 용어 사전 | p.2, p.3, p.5 |
| 도메인 모델 | p.2, p.4, p.5 |
| P-RESERVATION-CREATE-01 예약 신청 | p.3 |
| P-RESERVATION-APPROVE-01 예약 승인 | p.3 |
| P-RESERVATION-CHECKOUT-01 장비 수령 | p.3 (일부 추론) |
| P-RESERVATION-RETURN-01 반납 | p.3 (미정의) |
| P-RESERVATION-CANCEL-01 취소·변경·노쇼 | p.3, p.5 (미정의) |
| 플로우차트 | F-RESERVATION-CREATE-01, F-RESERVATION-APPROVE-01, F-RESERVATION-CHECKOUT-01 |

## 검증 메모

- `scripts/check_links.py`로 상대 링크 138개와 앵커를 검사해 깨진 링크 0건을 확인했습니다.
- finding 10개, 프로세스 5개, 플로우 5개의 ID와 앵커 중복은 없습니다.

## 확인하지 못한 것

- 원문이 Markdown이라 PDF·DOCX 변환 손실은 검증하지 않았습니다.
- 실제 화면 디자인, API 명세, 권한 매트릭스는 문서에 없습니다.
- 예약 수량과 재고의 관계, 외부 캘린더 제공자, 데이터 보존 요구사항은 추가 확인이 필요합니다.

## 다음 단계

1. V-PROC-RETURN-01, V-STATUS-OVERDUE-01를 닫을 반납·연체 정책을 결정합니다.
2. V-PERM-APPROVER-01, V-PROC-APPROVAL-01의 승인자·SLA를 결정합니다.
3. V-TERM-RESERVATION-01, V-DATA-INVENTORY-01, V-TERM-EQUIPMENT-01의 용어·데이터 모델을 보정합니다.
4. V-PROC-CANCEL-01, V-INT-CALENDAR-01, V-DATA-RETENTION-01의 1차 출시 범위를 결정합니다.
5. 결정이 반영되면 `glossary.md`, `domain.md`, `processes.md`, `flows.md`를 갱신합니다.
