# 프로세스 정의

> 문서 지도: [index](index.md) · [source](source.md) · [glossary](glossary.md) · [domain](domain.md) · [processes](processes.md) · [flows](flows.md) · [validation](validation.md)

AS-IS는 메신저와 엑셀을 사용하고, TO-BE는 웹 화면에서 예약·승인·대여·반납을 처리합니다. 원문에는 TO-BE 흐름만 구체적으로 기술되어 있습니다.

<a id="p-reservation-create-01" name="p-reservation-create-01"></a>
## P-RESERVATION-CREATE-01 예약 신청

| 항목 | 내용 |
| --- | --- |
| 프로세스 ID | P-RESERVATION-CREATE-01 |
| 이름 | 예약 신청 |
| 구분 | TO-BE |
| 액터 | 임직원, 시스템, 승인자(알림 수신) |
| 트리거 | 임직원이 예약 화면에서 신청 |
| 사전 조건 | 로그인, 예약 가능한 장비 선택 |
| 입력 | 장비, 시작일, 종료일, 수량, 사용 목적 |
| 단계 | 1. 장비 목록 조회 2. 기간·수량 선택 3. 재고 확인 4. 예약 생성 5. 승인자 알림 |
| 결정 | 재고 있음/없음, 중복 예약 여부 |
| 예외 | 재고 없음 → 대기 예약 안내, 중복 → 기존 예약 우선 |
| 사후 조건 | ReservationStatus.REQUESTED 생성, 승인자 알림 |
| 관련 용어 | 예약, 재고, 대기 예약, 장비 |
| 출처 | p.3 |
| 관련 문서 | [플로우 F-RESERVATION-CREATE-01](flows.md#f-reservation-create-01), [검증 V-DATA-INVENTORY-01](validation.md#v-data-inventory-01) |

<a id="p-reservation-approve-01" name="p-reservation-approve-01"></a>
## P-RESERVATION-APPROVE-01 예약 승인

| 항목 | 내용 |
| --- | --- |
| 프로세스 ID | P-RESERVATION-APPROVE-01 |
| 이름 | 예약 승인 |
| 구분 | TO-BE |
| 액터 | 승인자(미정의), 시스템 |
| 트리거 | 예약 신청 알림 |
| 사전 조건 | REQUESTED 예약 존재 |
| 입력 | 예약 내용, 신청자, 장비, 기간 |
| 단계 | 1. 예약 검토 2. 승인 또는 반려 3. 상태 변경 4. 신청자 알림 |
| 결정 | 승인/반려 |
| 예외 | 미응답, 승인자 부재, 반려 사유 누락 |
| 사후 조건 | APPROVED 또는 REJECTED, 신청자 알림 |
| 관련 용어 | 승인, 승인자, 반려 |
| 출처 | p.3 |
| 관련 문서 | [플로우 F-RESERVATION-APPROVE-01](flows.md#f-reservation-approve-01), [검증 V-PERM-APPROVER-01](validation.md#v-perm-approver-01), [검증 V-PROC-APPROVAL-01](validation.md#v-proc-approval-01) |

- 승인자 역할, 승인 SLA, 반려 사유 코드가 정의되지 않았습니다.
- 미응답 시 자동 승인·자동 반려·에스컬레이션 중 무엇을 할지 정해야 합니다.

<a id="p-reservation-checkout-01" name="p-reservation-checkout-01"></a>
## P-RESERVATION-CHECKOUT-01 장비 수령·대여

| 항목 | 내용 |
| --- | --- |
| 프로세스 ID | P-RESERVATION-CHECKOUT-01 |
| 이름 | 장비 수령·대여 |
| 구분 | TO-BE |
| 액터 | 임직원, 운영자 |
| 트리거 | 승인된 예약의 수령 |
| 사전 조건 | APPROVED 예약 |
| 입력 | 예약 ID, 장비 |
| 단계 | 1. 승인 예약 확인 2. 장비 수령 3. 대여 상태 변경 |
| 결정 | - |
| 예외 | 예약과 다른 장비 지급, 수령 지연, 미수령 |
| 사후 조건 | ReservationStatus.CHECKED_OUT |
| 관련 용어 | 대여, 수령, 운영자 |
| 출처 | p.3 (일부 추론) |
| 관련 문서 | [플로우 F-RESERVATION-CHECKOUT-01](flows.md#f-reservation-checkout-01), [검증 V-TERM-RESERVATION-01](validation.md#v-term-reservation-01) |

- 원문은 "운영자에게서 장비를 수령한다"만 기술하고, 상태 변경 주체와 확인 절차를 명시하지 않았습니다.

<a id="p-reservation-return-01" name="p-reservation-return-01"></a>
## P-RESERVATION-RETURN-01 반납

| 항목 | 내용 |
| --- | --- |
| 프로세스 ID | P-RESERVATION-RETURN-01 |
| 이름 | 반납 |
| 구분 | TO-BE |
| 액터 | 운영자 |
| 트리거 | 반납 예정일 또는 실제 반납 |
| 사전 조건 | CHECKED_OUT 예약 |
| 입력 | 예약 ID, 장비 상태 |
| 단계 | **미정의**. 원문은 "운영자가 처리한다"만 기술 |
| 결정 | 정상/연체/파손 여부 |
| 예외 | 연체, 파손, 분실, 부분 반납 |
| 사후 조건 | RETURNED (정상 반납 시) |
| 관련 용어 | 반납, 연체 |
| 출처 | p.3 |
| 관련 문서 | [검증 V-PROC-RETURN-01](validation.md#v-proc-return-01), [검증 V-STATUS-OVERDUE-01](validation.md#v-status-overdue-01) |

- 반납 절차, 상태 전이, 연체 판정, 파손·분실 처리, 알림 정책이 없습니다.
- 이 프로세스가 비어 있어 예약 생명주기를 닫을 수 없습니다.

<a id="p-reservation-cancel-01" name="p-reservation-cancel-01"></a>
## P-RESERVATION-CANCEL-01 취소·변경·노쇼

| 항목 | 내용 |
| --- | --- |
| 프로세스 ID | P-RESERVATION-CANCEL-01 |
| 이름 | 취소·변경·노쇼 |
| 구분 | TO-BE |
| 액터 | 임직원, 운영자, 시스템 |
| 트리거 | 취소 요청, 기간 변경, 수령 기한 초과 |
| 사전 조건 | REQUESTED 또는 APPROVED 예약 |
| 단계 | **미정의** |
| 결정 | 취소 가능 시점, 변경 가능 조건, 노쇼 판정 |
| 예외 | 승인 후 취소, 대여 중 변경, 반복 노쇼 |
| 사후 조건 | CANCELED 또는 NO_SHOW (상태 미정의) |
| 관련 용어 | 취소, 변경, 노쇼, 연체 |
| 출처 | p.3, p.5 (미정 사항) |
| 관련 문서 | [검증 V-PROC-CANCEL-01](validation.md#v-proc-cancel-01) |

- 1차 출시 범위에 포함할지부터 결정해야 합니다.
- 포함한다면 예약 상태에 CANCELED, NO_SHOW, OVERDUE를 추가해야 합니다.

## 프로세스 간 관계

- P-RESERVATION-CREATE-01에서 생성된 REQUESTED 예약이 P-RESERVATION-APPROVE-01의 입력입니다.
- P-RESERVATION-APPROVE-01에서 APPROVED된 예약만 P-RESERVATION-CHECKOUT-01의 입력이 됩니다.
- P-RESERVATION-CHECKOUT-01의 CHECKED_OUT 예약만 P-RESERVATION-RETURN-01의 입력이 됩니다.
- P-RESERVATION-CANCEL-01는 P-RESERVATION-CREATE-01·P-RESERVATION-APPROVE-01·P-RESERVATION-CHECKOUT-01·P-RESERVATION-RETURN-01의 상태에 개입하므로, 정책 확정 전에는 구현 순서를 정하기 어렵습니다.
