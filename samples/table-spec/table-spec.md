# 테이블 명세서

- 프로젝트: Sample DB
- 생성 시각: 2026-10-31T19:10:52+09:00
- SQL 방언: postgres
- 원본: DDL 파일 1개
- 테이블: 3
- 컬럼: 14
- 관계: 2
- 인덱스: 3

> 이 문서는 SQL DDL을 기준으로 생성했습니다. 런타임 DB 상태와 다를 수 있습니다.

## 테이블 목록

| No | 스키마 | 테이블 | 설명 | 컬럼 | PK | FK | 인덱스 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | - | projects | 프로젝트 | 4 | id | 1 | 1 |
| 2 | - | teams | 팀 | 3 | id | 0 | 0 |
| 3 | - | users | 사용자 | 7 | id | 1 | 2 |

## projects — 프로젝트

- 스키마: -
- 원본: samples/table-spec/schema.sql

| No | 컬럼 | 데이터 타입 | 길이 | PK | FK | UNIQUE | NOT NULL | DEFAULT | 설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | id | BIGSERIAL | - | Y | - | - | Y | - | - | - |
| 2 | owner_id | BIGINT | - | - | Y | - | Y | - | 소유자 | - |
| 3 | slug | VARCHAR | 80 | - | - | Y | Y | - | URL slug | - |
| 4 | title | VARCHAR | 200 | - | - | - | Y | - | - | - |

### 관계

| FK | 컬럼 | 참조 테이블 | 참조 컬럼 | ON DELETE | ON UPDATE |
| --- | --- | --- | --- | --- | --- |
| fk_projects_owner | owner_id | users | id | - | - |

### 인덱스

| 인덱스 | UNIQUE | 컬럼 |
| --- | --- | --- |
| uq_projects_slug | Y | slug |

## teams — 팀

- 스키마: -
- 원본: samples/table-spec/schema.sql

| No | 컬럼 | 데이터 타입 | 길이 | PK | FK | UNIQUE | NOT NULL | DEFAULT | 설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | id | BIGSERIAL | - | Y | - | - | Y | - | - | - |
| 2 | name | VARCHAR | 100 | - | - | - | Y | - | 팀 이름 | - |
| 3 | created_at | TIMESTAMPTZ | - | - | - | - | Y | CURRENT_TIMESTAMP | - | - |

## users — 사용자

- 스키마: -
- 원본: samples/table-spec/schema.sql

| No | 컬럼 | 데이터 타입 | 길이 | PK | FK | UNIQUE | NOT NULL | DEFAULT | 설명 | 비고 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | id | BIGSERIAL | - | Y | - | - | Y | - | - | - |
| 2 | email | VARCHAR | 255 | - | - | Y | Y | - | 로그인 이메일 | - |
| 3 | name | VARCHAR | 100 | - | - | - | Y | - | - | - |
| 4 | team_id | BIGINT | - | - | Y | - | Y | - | 소속 팀 | - |
| 5 | status | VARCHAR | 20 | - | - | - | Y | 'active' | - | CHECK status IN ('active', 'blocked') |
| 6 | created_at | TIMESTAMPTZ | - | - | - | - | Y | CURRENT_TIMESTAMP | - | - |
| 7 | last_login_at | TIMESTAMPTZ | - | - | - | - | - | - | 마지막 로그인 | - |

### 관계

| FK | 컬럼 | 참조 테이블 | 참조 컬럼 | ON DELETE | ON UPDATE |
| --- | --- | --- | --- | --- | --- |
| fk_users_team_id | team_id | teams | id | CASCADE | - |

### 인덱스

| 인덱스 | UNIQUE | 컬럼 |
| --- | --- | --- |
| idx_users_team | - | team_id |
| uq_users_email | Y | email |
