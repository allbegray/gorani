---
name: gorani-ddl-format
description: pg_dump·mysqldump가 만든 dump SQL을 PK·FK·UNIQUE·INDEX·COMMENT가 CREATE TABLE 안에 정리된 사람이 작성한 스타일의 DDL로 바꾼다. dump가 지저분해 읽기 어렵거나, 스키마 정의서·마이그레이션 기준 DDL이 필요할 때 사용.
metadata:
  version: "3.22.0"
  updated: "2026-11-12"
---

# DDL 정리

DB에서 뽑은 dump SQL을 **사람이 손으로 쓴 것처럼 읽기 좋은 DDL**로 바꿉니다. dump에 섞인 `SET`, `OWNER TO`, 데이터 블록, 시퀀스 보정을 걷어내고, 테이블 밖으로 흩어진 PK·FK·UNIQUE·CHECK를 `CREATE TABLE` 안으로 모읍니다.

## 전제

- Python 3가 필요합니다. 표준 라이브러리만 쓰므로 추가 패키지를 설치하지 않습니다.
- 입력은 `pg_dump`·`mysqldump`가 만든 SQL 파일, 또는 같은 형태의 손으로 쓴 DDL입니다.
- PostgreSQL과 MySQL을 1차 지원합니다. SQLite·MSSQL·Oracle은 같은 문법 범위에서만 동작합니다.
- 이 스킬은 dump 파일만 읽고 DB에 접속하지 않습니다. DB에 직접 붙어야 하면 DB에서 dump를 먼저 뜹니다.
- 변환 결과는 **스키마 정의**입니다. 데이터 INSERT·COPY, 함수·프로시저·트리거·뷰 본문은 결과에 넣지 않습니다.
- 결과 DDL을 실행해 검증하지 않으면 완료로 보고하지 않습니다.

## 절차

1. dump 파일을 확인합니다. 파일이 여러 개면 `--input`을 여러 번 주거나 디렉터리를 줍니다.
2. 방언을 확인합니다. `pg_dump` 결과면 `postgres`, `mysqldump`면 `mysql`입니다. 모르면 생략하고 `auto`에 맡깁니다.

   `python3 <스킬 폴더>/scripts/ddl_format.py --input dump.sql --outdir docs/db --name schema`

3. 출력 JSON의 `tables`, `columns`, `warnings`, `skipped_statements`를 확인합니다.
4. `schema.review.md`에서 빠진 객체(함수·뷰·트리거)와 경고를 읽습니다. 경고가 있으면 원본 dump의 해당 행을 확인합니다.
5. 결과 `schema.sql`을 실제 DB의 **빈 스키마**에 실행해 오류가 없는지 확인합니다.

   `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f docs/db/schema.sql`

6. 원본과 구조가 같은지 컬럼 수·제약 수를 대조합니다. `--model-out`의 `summary`와 원본 DB의 `information_schema`를 비교합니다.
7. 결과를 스키마 정의서나 마이그레이션 기준으로 씁니다.

## 입력과 옵션

### 입력

- `--input`은 SQL 파일 또는 디렉터리입니다. 여러 번 지정할 수 있습니다.
- 디렉터리에서는 `.sql`, `.ddl` 파일을 재귀 수집합니다.
- `--dialect`는 `auto`, `postgres`, `mysql`, `sqlite`, `mssql`, `oracle` 중 하나입니다. 기본 `auto`는 dump 머리말과 타입 이름으로 판별합니다.
- 파일 인코딩은 UTF-8을 우선하고, 실패하면 latin-1로 읽습니다.

### 출력

- `--formats`는 `sql`, `review` 조합입니다. 기본 `sql,review`입니다.
- `--outdir` 기본값은 `docs/db`, `--name` 기본값은 `schema`입니다.
- `--model-out PATH`는 렌더링 전 리포트 모델 JSON을 저장합니다.
- `--generated-at`은 생성 시각을 ISO 8601로 고정합니다.
- `--strict`는 경고가 있을 때 exit 1입니다.

### 스타일

| 옵션 | 기본 | 내용 |
| --- | --- | --- |
| `--comments` | `inline` | `inline`은 COMMENT ON·COMMENT '', `text`는 주석 줄, `off`는 주석 생략 |
| `--strip-schema` | postgres면 `public` | 출력에서 생략할 스키마 |
| `--keep-schema` | 꺼짐 | 스키마를 그대로 표시 |
| `--keep-names` | 꺼짐 | pg_dump가 만든 제약·인덱스 이름을 그대로 둠 |
| `--no-serial` | 꺼짐 | `bigint + nextval`을 `bigserial`로 바꾸지 않음 |
| `--no-align` | 꺼짐 | 컬럼 타입 시작 위치를 세로로 맞추지 않음 |
| `--no-header` | 꺼짐 | 결과 맨 위 머리말 주석 생략 |
| `--title`, `--database` | 빈 값 | 머리말에 넣을 설명과 DB 이름 |

## 출력 형식

### schema.sql

사람이 작성한 스타일의 DDL입니다.

- 테이블 하나를 한 블록으로 두고 블록 사이를 빈 줄로 나눕니다.
- 컬럼명과 타입 시작 위치를 세로로 맞춥니다.
- 단일 컬럼 PK·UNIQUE·FK·CHECK는 해당 컬럼 줄에 붙입니다.
- 여러 컬럼이 걸린 PK·UNIQUE·FK·CHECK는 `CREATE TABLE` 안 `CONSTRAINT` 줄로 둡니다.
- PostgreSQL의 INDEX는 `CREATE TABLE` 바로 뒤에 `CREATE INDEX`로 묶습니다. PostgreSQL에는 테이블 안 INDEX 문법이 없으므로, 테이블·COMMENT·INDEX를 한 블록으로 붙여 둡니다. INDEX 사이에는 빈 줄을 넣지 않습니다.
- MySQL의 `KEY`·`UNIQUE KEY`는 테이블 안에 둡니다.
- PostgreSQL COMMENT는 테이블 블록 바로 뒤 `COMMENT ON`으로 둡니다. MySQL은 컬럼·테이블 `COMMENT` 절로 둡니다.
- FK 참조 대상이 먼저 오도록 테이블 순서를 재배열합니다. 순환 참조는 이름 순으로 둡니다.
- pg_dump가 만든 `users_pkey`, `users_email_key`, `users_team_id_fkey` 같은 이름을 `pk_users`, `uq_users_email`, `fk_users_team_id`로 바꿉니다.
- PostgreSQL ENUM은 `CREATE TYPE ... AS ENUM`으로 결과 맨 위에 둡니다.
- `bigint` + `nextval(...)`은 `bigserial`로 바꾸고, `GENERATED ... AS IDENTITY`는 그대로 둡니다.

### schema.review.md

변환에서 빠진 객체와 경고를 정리합니다.

- 요약: 테이블·컬럼·FK·인덱스·CHECK·UNIQUE·경고·건너뛴 문장 수
- 바뀐 이름: dump가 만든 이름과 변환된 이름의 대응표
- 변환에서 빠진 객체: ENUM·시퀀스·스키마·그 밖의 문장
- 경고: 해석하지 못한 문장과 행 번호
- 확인할 것: 실행 검증·구조 대조 안내

## 변환 규칙

### 걷어내는 것

- `SET`, `SELECT pg_catalog.set_config`, `\restrict`, `\unrestrict`
- `ALTER TABLE ... OWNER TO`, `ALTER SEQUENCE ... OWNER TO`
- MySQL의 `/*!40101 SET ... */` 조건부 주석
- `LOCK TABLES`, `UNLOCK TABLES`, `DROP TABLE IF EXISTS`
- `COPY ... FROM stdin` 데이터 블록, `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`
- `GRANT`, `REVOKE`, `CREATE ROLE`, `CREATE DATABASE`
- `SELECT pg_catalog.setval`
- 뷰·함수·프로시저·트리거 생성문

### 테이블 안으로 모으는 것

- `ALTER TABLE ONLY ... ADD CONSTRAINT ... PRIMARY KEY` → 컬럼 인라인 또는 `CONSTRAINT ... PRIMARY KEY`
- `ADD CONSTRAINT ... UNIQUE` → 컬럼 인라인 `UNIQUE` 또는 `CONSTRAINT ... UNIQUE`
- `ADD CONSTRAINT ... FOREIGN KEY` → 컬럼 인라인 `REFERENCES` 또는 `CONSTRAINT ... FOREIGN KEY`
- `ADD CONSTRAINT ... CHECK` → 컬럼 인라인 `CHECK` 또는 `CONSTRAINT ... CHECK`
- `CREATE INDEX` → PostgreSQL은 테이블 블록 안(테이블·COMMENT 뒤)에, MySQL은 테이블 안 `KEY`

### 타입·표현식 정리

- `character varying(255)` → `varchar(255)`
- `timestamp with time zone` → `timestamptz`
- `timestamp without time zone` → `timestamp`
- `'active'::character varying` → `'active'`
- `(0)::numeric` → `0`
- `col = ANY (ARRAY['a','b'])` → `col IN ('a','b')`
- `now ()` → `now()`
- `bigint` + `nextval('..._seq'::regclass)` → `bigserial`
- MySQL의 `bigint unsigned`는 그대로 둡니다.

## 리포트 모델

`--model-out PATH`로 렌더링 전 데이터를 JSON으로 저장합니다.

| 필드 | 내용 |
| --- | --- |
| `schema_version` | 모델 스키마 버전 |
| `meta` | `generated_at`, `dialect`, `files`, `generator`, `options` |
| `summary` | 테이블·컬럼·FK·인덱스·CHECK·UNIQUE·경고·건너뛴 문장 수 |
| `tables` | 테이블별 컬럼 수, PK, FK, UNIQUE, CHECK, INDEX |
| `enums` | PostgreSQL ENUM 타입과 값 |
| `sequences` | dump에서 만난 시퀀스 이름 |
| `schemas` | dump에서 만난 `CREATE SCHEMA` 이름 |
| `warnings` | 경고 문자열 목록 |
| `outputs` | 생성한 산출물 경로 |

## 스크립트 구조

- `scripts/ddl_format.py`: CLI 진입점 (얇은 래퍼)
- `scripts/ddl_format/`: `cli`, `parse`, `model`, `render_sql`, `render_review`, `tokenizer`, `verify`, `constants`
- `tokenizer.py`는 문자열 리터럴·달러 인용·주석·괄호를 지키며 문장과 항목을 나눕니다. 이 모듈이 dump를 안전하게 자르는 핵심입니다.
- `parse.py`는 dump 문장을 테이블 구조로 해석합니다. 모르는 문장은 버리지 않고 `warnings`에 남깁니다.
- `render_sql.py`는 테이블 구조를 사람이 읽는 DDL로 렌더링합니다.
- `model.py`는 이름 정규화·타입 별칭·표현식 정리를 맡습니다. 표준 라이브러리만 씁니다.
- `selftest.py`는 DB 없이 돌리는 회귀 검증입니다. `python3 skills/gorani-ddl-format/scripts/selftest.py`로 56개 항목을 확인합니다.

## 실패 처리

- 테이블을 0개 찾으면 dump 파일인지, `--dialect`가 맞는지 확인합니다. 결과를 완료로 보고하지 않습니다.
- `warnings`가 있으면 `schema.review.md`의 행 번호로 원본을 확인합니다. 해석하지 못한 문장을 임의로 추측해 채우지 않습니다.
- FK 참조 대상 테이블을 찾지 못하면 `schema.sql`에 그대로 `REFERENCES`를 남기고, 실행 검증에서 오류로 드러납니다.
- 결과 DDL 실행이 실패하면 오류 문장과 원본 dump의 해당 부분을 함께 보고합니다. dump를 고쳐 다시 변환합니다.
- MySQL에서 `SET FOREIGN_KEY_CHECKS=0`이 필요할 만큼 순서가 꼬이면, FK 재배열이 실패한 것이므로 `schema.sql`의 테이블 순서와 FK를 확인합니다.
- 파일 인코딩이 깨지면 `schema.review.md`의 주석을 확인하고 원본을 UTF-8로 다시 저장합니다.
- `--strict`로 exit 1이 나오면 실패가 아니라 경고가 있다는 뜻입니다.

## 금지

- dump에 없는 컬럼·제약·설명을 사실처럼 만들지 않습니다.
- 데이터 INSERT·COPY를 결과 DDL에 넣지 않습니다.
- 해석하지 못한 문장을 조용히 버리지 않습니다. `warnings`와 검토 md에 남깁니다.
- 결과 DDL을 실제 DB에 실행하지 않고 "검증 완료"라고 보고하지 않습니다.
- 운영 DB에 결과 DDL을 그대로 실행하지 않습니다. 빈 스키마나 개발 DB에서 먼저 검증합니다.
- 원본 dump 파일을 덮어쓰지 않습니다.
- DB 비밀번호·연결 문자열을 결과·로그·문서에 남기지 않습니다.
- 사용자 지시 없이 커밋·푸시·PR을 만들지 않습니다.
- 고객 정보, 내부 URL, 시크릿을 문서에 넣지 않습니다.

## 도구 설치

이 스킬은 Python 3 표준 라이브러리만 사용합니다. 추가 패키지를 설치하지 않습니다.

- 검증 단계에서 `psql`·`mysql` 클라이언트가 필요할 수 있습니다.
- 필요한 클라이언트가 없으면 OS 패키지 관리자로 설치를 시도합니다. macOS는 `brew install postgresql@17`·`brew install mysql-client`, Debian/Ubuntu는 `apt-get install postgresql-client`·`default-mysql-client`입니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 거부하면 실행 검증을 하지 않고 그 사실을 결과에 적습니다.
- `sudo`가 필요하면 `sudo -n`으로만 시도하고 암호 입력을 요구하지 않습니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리를 쓰지 않습니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 문서·고객 데이터를 설치 과정에서 외부로 보내지 않습니다.

## 문제 보고

스킬이 예상과 다르게 실패하거나 개선점·아이디어·양식 제안이 보이면, 원인이 이 스킬·스크립트에 있는지 확인한 뒤 `gorani-report`로 GitHub 이슈를 만들지 사용자에게 먼저 묻습니다. 공개 이슈에는 고객 정보·시크릿·내부 URL을 넣지 않고, 사용자 확인 후 작성합니다.
