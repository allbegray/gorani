---
name: gorani-table-spec
description: SQL DDL 또는 실제 DB에서 테이블·컬럼·PK/FK·인덱스·설명을 추출해 테이블 명세서를 Excel, Markdown, HTML로 만든다. DB 스키마 문서화, 테이블 정의서 작성, 릴리스 전 스키마 검토가 필요할 때 사용.
metadata:
  version: "3.17.0"
  updated: "2026-10-31"
---

# 테이블 명세서 생성

SQL DDL 파일 또는 실제 데이터베이스에서 테이블 정의를 읽어 **테이블 목록, 컬럼 명세, 관계, 인덱스**를 Excel, Markdown, HTML로 정리합니다. DB에 쓸 때는 읽기 전용 계정을 사용합니다.

## 전제

- Python 3가 필요합니다.
- DDL 모드에는 `sqlglot`이 필요합니다.
- DB 모드에는 `SQLAlchemy`와 해당 DB 드라이버가 필요합니다.
- `xlsx`를 선택할 때만 `openpyxl`이 필요합니다.
- DB 모드는 접속 시점의 스키마를 읽습니다. 데이터 자체, 실행 계획, 통계, 권한 정책은 조회하지 않습니다.
- DB 모드는 기본 스키마만 조회합니다. 다른 스키마는 `--schema`로 지정합니다.
- DDL 모드는 `CREATE TABLE`, `ALTER TABLE`, `COMMENT ON`, `CREATE INDEX`, `DROP TABLE`을 지원합니다.
- 이 스킬은 스키마를 수정하지 않습니다. DB 계정은 SELECT·메타데이터 조회 권한만 있는 읽기 전용 계정을 권장합니다.

## 절차

1. 입력 방식을 정합니다. SQL 파일이면 DDL 모드, 실제 DB면 DB 모드입니다. 생성할 산출물도 Excel·Markdown·HTML 중에서 먼저 묻습니다.
2. DDL 모드:
   - DDL 파일 또는 디렉터리를 확인합니다. 마이그레이션이 여러 파일이면 시간 순서대로 정렬되는지 확인합니다.
   - PostgreSQL이면 `--dialect postgres`, MySQL이면 `--dialect mysql`을 씁니다.
3. DB 모드:
   - 읽기 전용 DB URL과 조회할 스키마를 확인합니다.
   - 비밀번호는 명령행에 직접 쓰지 말고 `$DATABASE_URL` 같은 환경변수로 넘깁니다.
4. 사용자가 고른 형식만 `--formats`에 넣어 테이블 명세서를 생성합니다.

   DDL:

   `python3 <스킬 폴더>/scripts/table_spec.py --ddl db/migrations --dialect postgres --project <프로젝트명> --outdir docs/db --name table-spec --formats xlsx,md,html`

   DB:

   `python3 <스킬 폴더>/scripts/table_spec.py --db-url "$DATABASE_URL" --schema public --project <프로젝트명> --outdir docs/db --name table-spec --formats xlsx,md,html`

5. 출력의 `tables`, `columns`, `foreign_keys`, `indexes`, `warnings`를 확인합니다.
6. `warnings`가 있으면 원본 DDL 또는 DB 스키마·권한을 확인합니다. `--strict`를 주면 경고가 있을 때 exit 1로 CI에서 차단할 수 있습니다.
7. 테이블·컬럼 설명은 입력에 있는 COMMENT만 사용합니다. 없으면 비워 두고 추측하지 않습니다.
8. `table-spec.artifact.json`의 `sources`가 실제 마이그레이션 경로와 맞는지 확인합니다. 다르면 `--sources`로 보정하고 다시 생성합니다.
9. DDL이 바뀌거나 DB 스키마가 바뀔 때 다시 생성합니다. `docs/db/table-spec.xlsx`를 배포 문서나 저장소 위키에 연결합니다.

## 입력

`--ddl`과 `--db-url` 중 하나만 지정합니다.

### DDL 모드

- `--ddl`은 SQL 파일 또는 디렉터리입니다. 디렉터리에서는 `.sql`, `.ddl` 파일을 재귀 수집합니다.
- `--dialect`는 `auto`, `postgres`, `mysql`, `sqlite`, `mssql`, `oracle` 중 하나입니다.
- `--ddl`을 여러 번 지정하면 파일을 합쳐서 해석합니다.

### DB 모드

- `--db-url`은 SQLAlchemy URL입니다.
  - PostgreSQL: `postgresql+psycopg://user:pass@host:5432/db`
  - MySQL: `mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4`
  - SQLite: `sqlite:///path/to.db`
  - MSSQL: `mssql+pyodbc://...`
  - Oracle: `oracle+oracledb://...`
- `--schema`는 조회할 스키마입니다. 여러 번 지정할 수 있습니다. 생략하면 DB 기본 스키마만 조회합니다.
- `--include-system`은 SQL Server의 `spt_*`, `MSreplication_options` 같은 시스템 테이블도 포함합니다. 기본은 제외합니다.
- DB URL에 비밀번호가 들어가면 결과의 원본 표시에서 마스킹됩니다. 그래도 명령행 기록에 남을 수 있으므로 환경변수를 권장합니다.

### 공통

- `--formats`는 `md,xlsx,html` 조합입니다. 기본은 `xlsx,md,html`입니다. 사용자가 고른 형식만 넣습니다.
- `--project`를 생략하면 현재 디렉터리 이름을 씁니다.
- `--sources`는 산출물 갱신 판단에 쓸 소스 글롭입니다. 생략하면 `--ddl` 경로를 사용합니다. DB 모드에서는 비어 있으므로 마이그레이션 글롭을 직접 지정하는 것을 권장합니다.
- `--no-manifest`는 sidecar `.artifact.json`을 만들지 않습니다.
- `--strict`는 경고를 실패로 처리합니다.

## 출력 형식

- `table-spec.xlsx`:
  - `요약`: 프로젝트, 생성 시각, SQL 방언, 원본, 테이블·컬럼·FK·인덱스 수, 경고 수
  - `테이블 목록`: 스키마, 테이블, 설명, 컬럼 수, PK, FK 수, 인덱스 수
  - `컬럼 명세`: 테이블·컬럼·타입·길이·PK·FK·UNIQUE·NOT NULL·DEFAULT·설명·비고
  - `관계`: FK 이름, 자식/부모 테이블·컬럼, ON DELETE/UPDATE
  - `인덱스`: 테이블, 인덱스, UNIQUE, 컬럼
  - `파싱 메모`: 경고와 원본
- `table-spec.md`: 같은 내용을 Markdown 표로 정리합니다. 테이블별 상세와 관계·인덱스를 포함합니다.
- `table-spec.html`: 자기완결 HTML입니다. 테이블 검색, 목차, 컬럼·관계·인덱스 표를 포함하고 외부 CSS·JS·폰트·이미지를 쓰지 않습니다.
- `table-spec.artifact.json`: 산출물 옆에 남기는 sidecar manifest. `sources`, `generated_commit`, `regenerate`를 기록해 `gorani-change-impact`가 갱신 필요 여부를 판단하게 합니다. DB 모드의 `regenerate`에는 `--db-url` 실제 값을 넣지 않고 `$DATABASE_URL`로 기록합니다.
- `--formats md` 또는 `--formats html`만 주면 openpyxl 없이 동작합니다.

### HTML

- 단일 파일입니다. CSS와 JavaScript를 인라인으로 넣고 외부 CDN·폰트·이미지를 쓰지 않습니다.
- `Content-Security-Policy`로 외부 요청을 막습니다.
- 구성: 요약 카드, 테이블 검색, 목차, 테이블별 컬럼·관계·인덱스 표.
- 검색은 테이블명·컬럼명·설명을 대상으로 동작합니다.
- 라이트·다크 모드, 모바일 폭, 인쇄를 지원합니다.
- 검토 메모가 있으면 페이지 하단에 표시합니다.

## 파싱 규칙

### DDL 모드

- 컬럼 타입은 `VARCHAR`와 길이 `255`처럼 분리합니다. `NUMERIC(10, 2)`는 `NUMERIC`과 `10, 2`로 표시합니다.
- PK는 컬럼 정의의 `PRIMARY KEY`와 테이블 제약의 `PRIMARY KEY (...)`를 모두 반영합니다.
- FK는 컬럼 정의의 `REFERENCES`와 테이블 제약의 `FOREIGN KEY ... REFERENCES`를 모두 반영합니다.
- UNIQUE는 단일 컬럼이면 컬럼에 `Y`, 복수 컬럼이면 인덱스 시트에 `UNIQUE=Y`로 표시합니다.
- MySQL의 인라인 `COMMENT '...'`, `COMMENT='...'`와 PostgreSQL의 `COMMENT ON TABLE/COLUMN`을 반영합니다.
- `AUTO_INCREMENT`, `CHECK`는 컬럼 비고에 기록합니다.
- `ALTER TABLE ... ADD/DROP/RENAME COLUMN`, `ALTER COLUMN TYPE/SET/DROP NOT NULL/SET DEFAULT`, `ADD CONSTRAINT`, `DROP CONSTRAINT`를 반영합니다.
- `CREATE INDEX`와 인라인 `KEY`/`INDEX`를 인덱스 시트에 반영합니다.

### DB 모드

- SQLAlchemy Inspector로 테이블·컬럼·PK·FK·UNIQUE·인덱스·COMMENT를 읽습니다.
- 기본 스키마가 아닌 스키마는 `--schema`로 지정합니다.
- 뷰, 시스템 스키마, 임시 테이블은 기본적으로 포함하지 않습니다. SQL Server 시스템 테이블은 `--include-system`으로 포함할 수 있습니다.
- DB가 COMMENT를 저장하지 않는 경우(SQLite 등) 설명은 비어 있습니다.
- `AUTO_INCREMENT`·시퀀스·생성 컬럼은 드라이버가 제공하는 범위에서만 표시합니다.
- DB 벤더별 타입은 SQLAlchemy가 반환하는 문자열을 기준으로 표시합니다.

## 제한

- DDL에 없는 컬럼 설명·업무 규칙·데이터 예시를 추측해서 채우지 않습니다.
- DB 모드는 접속 시점의 스키마만 반영합니다. 이후 변경은 다시 생성해야 합니다.
- DB 계정 권한이 부족하면 일부 테이블·주석·인덱스가 누락될 수 있습니다.
- 뷰, 트리거, 저장 프로시저, 동적 SQL, `CREATE TABLE ... AS SELECT`는 테이블 명세 대상이 아닙니다.
- `auto` 방언은 문법이 비슷한 DDL에서 잘못 선택될 수 있습니다. 결과가 이상하면 `--dialect`를 명시합니다.

## 실패 처리

- DDL 모드에서 `sqlglot`이 없으면 아래 `## 도구 설치` 원칙에 따라 설치를 시도하고, 실패하면 설치 명령과 이유를 보고합니다.
- DB 모드에서 `SQLAlchemy`가 없으면 설치를 시도합니다. 드라이버가 없으면 DB 종류에 맞는 드라이버 설치 명령을 보고합니다.
- DB 연결·인증·권한 오류가 나면 비밀번호를 출력하지 말고 호스트·DB·계정·오류 유형만 보고합니다.
- SQL 파싱이 실패하면 파일 경로와 오류를 보고합니다. `--dialect`를 바꿔 다시 실행하거나 문제 SQL을 확인합니다.
- 테이블을 0개 찾으면 `--ddl`·`--db-url`·`--schema`와 권한을 확인하고, 결과를 완료로 보고하지 않습니다.
- `xlsx`를 선택했는데 openpyxl이 없으면 설치를 시도합니다. 설치를 거부하면 `--formats md` 또는 `--formats html`로 생성합니다.
- `--strict`로 exit 1이 나오면 실패가 아니라 경고가 있다는 뜻입니다. `파싱 메모`와 원본을 확인합니다.
- 경고를 없애기 위해 입력에 없는 내용을 임의로 채우지 않습니다.

## 도구 설치

필요한 프로그램이 없으면 자동 설치를 시도합니다.

- OS 패키지 관리자(macOS `brew`, Debian/Ubuntu `apt-get`, Fedora `dnf`, Arch `pacman`, Windows `winget`·`choco`·`scoop`)와 언어 패키지 관리자(`uv`·`pipx`·`npm`·`cargo`·`go`)를 우선합니다.
- DDL 모드: `sqlglot`.
- DB 모드: `sqlalchemy`와 DB 드라이버.
  - PostgreSQL: `psycopg[binary]`
  - MySQL: `pymysql`
  - SQLite: Python 기본 `sqlite3`
  - MSSQL: `pyodbc`와 ODBC 드라이버
  - Oracle: `oracledb`
- xlsx: `openpyxl`.
- 작업에 필요한 도구만 설치합니다. 무관한 패키지나 전체 도구 묶음을 설치하지 않습니다.
- 설치 전에 도구와 명령을 알립니다. 사용자가 설치를 거부하면 설치하지 않고 대체 도구나 입력 파일을 요청합니다.
- 사용자 권한 설치를 우선합니다. `sudo`가 필요하면 `sudo -n`으로만 시도하고 암호 입력을 요구하지 않습니다. 실패하면 실행할 명령과 이유를 보고합니다.
- 공식 패키지·저장소만 사용합니다. `curl | sh`, 출처 불명 바이너리, 임의 URL 다운로드·실행을 금지합니다.
- 설치 후 `command -v`와 `--version`으로 확인합니다. 실패하면 대체 도구를 쓰거나 입력 파일을 요청합니다.
- 설치한 도구·버전·실패 사유를 결과나 evidence에 기록합니다.
- 문서·고객 데이터를 설치 과정에서 외부로 보내지 않습니다.
- GUI 앱·드라이버·커널·서비스처럼 시스템 변경이 큰 설치는 먼저 확인합니다.

## 금지

- DDL·DB에 없는 컬럼·설명·관계를 사실처럼 만들지 않습니다.
- DB 스키마·데이터·권한을 수정하지 않습니다. 쓰기 권한이 있는 계정을 사용하지 않습니다.
- DB 비밀번호·연결 문자열 전체를 결과·로그·문서에 남기지 않습니다.
- DDL·코드·DB 스키마를 수정하지 않습니다.
- 사용자 지시 없이 커밋·푸시·PR을 만들지 않습니다.
- 고객 정보, 내부 URL, 시크릿을 문서에 넣지 않습니다.
- 경고를 숨기기 위해 결과를 임의로 편집하지 않습니다.

## 문제 보고

스킬이 예상과 다르게 실패하거나 개선점·아이디어·양식 제안이 보이면, 원인이 이 스킬·스크립트에 있는지 확인한 뒤 `gorani-report`로 GitHub 이슈를 만들지 사용자에게 먼저 묻습니다. 공개 이슈에는 고객 정보·시크릿·내부 URL을 넣지 않고, 사용자 확인 후 작성합니다.
