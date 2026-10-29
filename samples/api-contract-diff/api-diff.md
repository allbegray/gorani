# API 계약 변경 리포트

**P1 4건 · 배포 전 수정 필요** — P2 7건을 포함해 기존 클라이언트가 깨질 수 있는 변경이 11건 있습니다.

- 서비스: Share API
- 비교: `samples/api-contract-diff/old.yaml` (v1.0.0) → `samples/api-contract-diff/new.yaml` (v1.1.0)
- 배포 버전: 1.1.0
- 영향 클라이언트: web, ios, android
- 생성 시각: 2026-10-29T23:57:08+09:00
- 우선순위: P0 전면 중단 · P1 배포 전 수정 · P2 배포 전 확인 · P3 호환성 확인 · P4 참고
- 집계: P0 0 · P1 4 · P2 7 · P3 8 · P4 3

## 먼저 확인할 것

1. **[P1]** **모든 API 호출에 인증이 필요해집니다.** 토큰 없이 호출하던 클라이언트는 401을 받습니다.
2. **[P1]** **요청에 `workspaceId` 필드가 필수가 됩니다.** 이 값을 보내지 않으면 요청이 실패합니다. — POST /shares
3. **[P1]** **`visibility`에서 `team` 값을 보낼 수 없습니다.** 이 값을 보내던 클라이언트는 요청이 실패할 수 있습니다. — POST /shares
4. **[P1]** **`limit` 파라미터가 필수가 됩니다.** 이 파라미터 없이 호출하면 실패합니다. — GET /shares
5. **[P2]** **응답에서 `ownerEmail` 필드가 제거됩니다.** 이 값을 표시하던 화면은 빈칸이 되거나 오류가 날 수 있습니다. — GET /shares, POST /shares, GET /shares/{id}
6. **[P2]** **`visibility`에서 `team` 값이 제거됩니다.** 이 값을 처리하던 화면은 오류가 날 수 있습니다. — GET /shares, POST /shares, GET /shares/{id}
7. **[P2]** **`404` 응답이 사라집니다.** 이 상태를 따로 처리하던 클라이언트는 동작이 달라집니다. — GET /shares/{id}

## API별 변경

### GET /shares — P1 · 배포 전 수정

- **P1 · 요청** `limit` 파라미터가 필수가 됩니다. 이 파라미터 없이 호출하면 실패합니다.
- **P2 · 응답 200** `ownerEmail` 필드가 제거됩니다. 이 값을 표시하던 화면은 빈칸이 되거나 오류가 날 수 있습니다.
- **P2 · 응답 200** `visibility`에서 `team` 값이 제거됩니다. 이 값을 처리하던 화면은 오류가 날 수 있습니다.
- **P3 · 응답 200** `title` 최대 길이가 200자에서 120자로 줄어듭니다. 120자를 넘는 값은 거부되거나 잘릴 수 있습니다.
- **P3 · 응답 200** `visibility`에 `public` 값이 추가됩니다. 새 값을 모르는 클라이언트는 오류가 날 수 있습니다.

**응답 200 예시 (이전 → 이후)**

`-` 이전 값, `+` 이후 값

```diff
 [
   {
     "id": "s-1",
-    "ownerEmail": "owner@example.com",
     "title": "Trip plan",
-    "visibility": "team"
+    "visibility": "private"
   }
 ]
```

### POST /shares — P1 · 배포 전 수정

- **P1 · 요청** `workspaceId` 필드가 필수가 됩니다. 이 값을 보내지 않으면 요청이 실패합니다.
- **P1 · 요청** `visibility`에서 `team` 값을 보낼 수 없습니다. 이 값을 보내던 클라이언트는 요청이 실패할 수 있습니다.
- **P2 · 응답 201** `ownerEmail` 필드가 제거됩니다. 이 값을 표시하던 화면은 빈칸이 되거나 오류가 날 수 있습니다.
- **P2 · 응답 201** `visibility`에서 `team` 값이 제거됩니다. 이 값을 처리하던 화면은 오류가 날 수 있습니다.
- **P3 · 요청** `title` 최대 길이가 200자에서 120자로 줄어듭니다. 120자를 넘는 값은 거부되거나 잘릴 수 있습니다.
- **P3 · 응답 201** `title` 최대 길이가 200자에서 120자로 줄어듭니다. 120자를 넘는 값은 거부되거나 잘릴 수 있습니다.
- **P3 · 응답 201** `visibility`에 `public` 값이 추가됩니다. 새 값을 모르는 클라이언트는 오류가 날 수 있습니다.
- **P4 · 요청** `visibility`에 `public` 값을 보낼 수 있습니다. 기존 클라이언트는 영향이 없습니다.

**요청 예시 (이전 → 이후)**

`-` 이전 값, `+` 이후 값

```diff
 {
   "title": "Trip plan",
-  "visibility": "team"
+  "visibility": "private",
+  "workspaceId": "ws-1"
 }
```

### GET /shares/{id} — P2 · 배포 전 확인

- **P2 · 응답 404** `404` 응답이 사라집니다. 이 상태를 따로 처리하던 클라이언트는 동작이 달라집니다.
- **P2 · 응답 200** `ownerEmail` 필드가 제거됩니다. 이 값을 표시하던 화면은 빈칸이 되거나 오류가 날 수 있습니다.
- **P2 · 응답 200** `visibility`에서 `team` 값이 제거됩니다. 이 값을 처리하던 화면은 오류가 날 수 있습니다.
- **P3 · SDK** SDK 메서드명이 `getShare`에서 `fetchShare`로 바뀝니다. SDK를 다시 생성하면 기존 호출 코드가 컴파일 오류를 낼 수 있습니다.
- **P3 · 응답 200** `title` 최대 길이가 200자에서 120자로 줄어듭니다. 120자를 넘는 값은 거부되거나 잘릴 수 있습니다.
- **P3 · 응답 200** `visibility`에 `public` 값이 추가됩니다. 새 값을 모르는 클라이언트는 오류가 날 수 있습니다.

### 새 경로 /shares/{id}/comments — P4 · 참고

- **P4 · API** `/shares/{id}/comments` 경로가 추가됩니다. 기존 API 동작은 바뀌지 않습니다.

## 공통 변경

- **P1 · 인증** 모든 API 호출에 인증이 필요해집니다. 토큰 없이 호출하던 클라이언트는 401을 받습니다.
- **P4 · 문서** 스펙 버전이 1.0.0에서 1.1.0으로 바뀝니다. 문서 버전만 바뀌었고 API 동작 변화는 아닙니다.

## 배포 전 체크리스트

- [ ] P1 변경 4건은 배포 전에 수정하거나 배포 순서를 조정
- [ ] P2 변경 7건은 실제 클라이언트 사용처와 대조
- [ ] P3 변경 8건은 파서·SDK·게이트웨이 정책과 함께 확인
- [ ] 서버와 클라이언트 배포 순서 결정 (서버 먼저 / 클라이언트 먼저 / API 버전 분리)
- [ ] 제거된 필드·enum 값·상태 코드를 사용하는 코드와 화면 검색
- [ ] 인증 없이 호출하는 경로와 토큰 갱신 흐름 확인

## 테스트 체크리스트

- [ ] 변경된 API의 정상·실패 응답 확인
- [ ] 요청 필수값을 빼고 호출했을 때 오류 확인
- [ ] 응답에서 빠진 필드·새 enum 값·새 상태 코드 처리 확인
- [ ] 토큰 없이 호출했을 때 401 확인

## 확인이 필요한 것

- 스펙에 없는 게이트웨이 정책, 실제 응답, 클라이언트 구현은 별도 확인

> 이 리포트는 스펙 비교 결과입니다. 런타임 동작과 실제 클라이언트 영향은 별도 검증이 필요합니다.

## 부록: 전체 변경 목록

| ID | 우선순위 | 위치 | 변경 |
| --- | --- | --- | --- |
| B-01 | P1 | GET /shares → 쿼리 파라미터 limit | `limit` 파라미터가 필수가 됩니다. |
| B-04 | P1 | POST /shares → 요청 본문 → workspaceId | `workspaceId` 필드가 필수가 됩니다. |
| B-05 | P1 | POST /shares → 요청 본문 → visibility | `visibility`에서 `team` 값을 보낼 수 없습니다. |
| B-11 | P1 | 인증 | 모든 API 호출에 인증이 필요해집니다. |
| B-02 | P2 | GET /shares → 응답 200 본문 → ownerEmail | `ownerEmail` 필드가 제거됩니다. |
| B-03 | P2 | GET /shares → 응답 200 본문 → visibility | `visibility`에서 `team` 값이 제거됩니다. |
| B-06 | P2 | POST /shares → 응답 201 본문 → ownerEmail | `ownerEmail` 필드가 제거됩니다. |
| B-07 | P2 | POST /shares → 응답 201 본문 → visibility | `visibility`에서 `team` 값이 제거됩니다. |
| B-08 | P2 | GET /shares/{id} → 응답 404 | `404` 응답이 사라집니다. |
| B-09 | P2 | GET /shares/{id} → 응답 200 본문 → ownerEmail | `ownerEmail` 필드가 제거됩니다. |
| B-10 | P2 | GET /shares/{id} → 응답 200 본문 → visibility | `visibility`에서 `team` 값이 제거됩니다. |
| R-01 | P3 | GET /shares → 응답 200 본문 → title 최대 길이 | `title` 최대 길이가 200자에서 120자로 줄어듭니다. |
| R-02 | P3 | GET /shares → 응답 200 본문 → visibility | `visibility`에 `public` 값이 추가됩니다. |
| R-03 | P3 | POST /shares → 요청 본문 → title 최대 길이 | `title` 최대 길이가 200자에서 120자로 줄어듭니다. |
| R-04 | P3 | POST /shares → 응답 201 본문 → title 최대 길이 | `title` 최대 길이가 200자에서 120자로 줄어듭니다. |
| R-05 | P3 | POST /shares → 응답 201 본문 → visibility | `visibility`에 `public` 값이 추가됩니다. |
| R-06 | P3 | GET /shares/{id} | SDK 메서드명이 `getShare`에서 `fetchShare`로 바뀝니다. |
| R-07 | P3 | GET /shares/{id} → 응답 200 본문 → title 최대 길이 | `title` 최대 길이가 200자에서 120자로 줄어듭니다. |
| R-08 | P3 | GET /shares/{id} → 응답 200 본문 → visibility | `visibility`에 `public` 값이 추가됩니다. |
| I-01 | P4 | 스펙 버전 | 스펙 버전이 1.0.0에서 1.1.0으로 바뀝니다. |
| N-01 | P4 | 경로 /shares/{id}/comments | `/shares/{id}/comments` 경로가 추가됩니다. |
| N-02 | P4 | POST /shares → 요청 본문 → visibility | `visibility`에 `public` 값을 보낼 수 있습니다. |
