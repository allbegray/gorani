# 용어 사전

> 문서 지도: [index](index.md) · [source.plain](source/source.plain.md) · [source](source/source.md) · [glossary](glossary.md) · [domain](domain.md) · [processes](processes.md) · [flows](flows.md) · [validation](validation.md)

| 용어 | 정의 | 동의어·약어 | 출처 | 상태 | 비고 | 관련 |
| --- | --- | --- | --- | --- | --- | --- |
| 장비 | 임직원이 예약해서 사용하는 물품. 노트북, 프로젝터, 카메라 | 자산 | p.2 | 확정 | `자산`과 같은 뜻으로 사용 | [P](processes.md#p-reservation-create-01), [V](validation.md#v-term-equipment-01) |
| 자산 | 장비와 같은 뜻 | 장비 | p.2 | 확정 | 화면·API 이름은 `equipment`로 통일 권장 | — |
| 예약 | 장비를 특정 기간 사용하겠다고 신청하는 것 | 대여 | p.2 | 모호 | 문서에 따라 `대여`와 혼용 | [P](processes.md#p-reservation-create-01), [F](flows.md#f-reservation-create-01), [V](validation.md#v-term-reservation-01) |
| 대여 | 예약한 장비를 실제로 수령해 사용하는 상태 | 예약 | p.2 | 충돌 | 예약과 대여를 같은 뜻으로 쓴 문장이 있음 | [P](processes.md#p-reservation-checkout-01), [F](flows.md#f-reservation-checkout-01) |
| 승인 | 예약 확정 전 승인자가 검토하는 절차 | - | p.2 | 확정 | 승인자·SLA는 미정의 | [P](processes.md#p-reservation-approve-01), [F](flows.md#f-reservation-approve-01) |
| 승인자 | 예약을 승인하거나 반려하는 역할 | - | p.2 | 미정의 | 누가 승인자인지, 운영자와 동일인 가능 여부만 언급 | — |
| 운영자 | 장비를 등록하고 대여·반납 상태를 변경하는 역할 | - | p.2 | 확정 | 반납 처리 권한의 범위가 불명확 | — |
| 관리자 | 전체 예약 내역을 조회하는 역할 | - | p.2 | 확정 | 조회 외 권한은 미정의 | — |
| 반납 | 대여한 장비를 운영자에게 돌려주는 것 | - | p.3 | 확정 | 반납 절차·상태 전이는 미정의 | [P](processes.md#p-reservation-return-01), [V](validation.md#v-proc-return-01) |
| 연체 | 반납 예정일을 넘긴 상태 | - | p.3 | 확정 | 연체 판정·알림·제재는 미정의 | [P](processes.md#p-reservation-return-01), [V](validation.md#v-status-overdue-01) |
| 재고 | 특정 기간에 예약 가능한 장비 수량 | 가용성 | p.3 | 미정의 | 기간·수량 기준이 명시되지 않음 | [P](processes.md#p-reservation-create-01), [V](validation.md#v-data-inventory-01) |
| 대기 예약 | 재고가 없을 때 만드는 예약 | 대기열 | p.3 | 미정의 | 생성·해제·우선순위 규칙 없음 | — |
| 예약 상태 | 신청, 승인, 반려, 대여, 반납 | - | p.5 | 모호 | 취소·연체·노쇼 상태가 없음 | [V](validation.md#v-status-overdue-01), [상태 전이](domain.md#상태-전이) |
| 노쇼 | 예약 후 수령하지 않은 상태 | - | p.5 | 미정의 | 미정 사항에만 언급 | [V](validation.md#v-proc-cancel-01) |
