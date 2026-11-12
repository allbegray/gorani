# gorani-ddl-format scripts

dump SQL → 테이블 구조 → 사람이 읽는 DDL 순서로 처리합니다.

```text
ddl_format.py               CLI 진입점 (얇은 래퍼)
ddl_format/
  cli.py                    argparse, 입력 수집, 출력 경로, 모델 저장
  parse.py                  dump 문장 → 테이블 구조 (표준 라이브러리)
  model.py                  이름 정규화, 타입 별칭, 표현식 정리
  tokenizer.py              문자열·주석·달러 인용을 지키는 문장 분리
  render_sql.py             사람이 읽는 DDL 렌더러
  render_review.py          검토 md 렌더러
  constants.py              방언·출력 형식 상수
selftest.py                 DB 없이 돌리는 회귀 검증 (56개 항목)
```

## 데이터 흐름

1. `tokenizer.py`가 COPY 데이터 블록을 걷어내고 문장을 나눕니다.
2. `parse.py`가 `CREATE TABLE`, `ALTER TABLE ... ADD CONSTRAINT`, `CREATE INDEX`, `COMMENT ON`을 해석해 테이블 구조를 만듭니다.
3. `model.py`가 타입 별칭·캐스트·제약 이름을 정리합니다.
4. `render_sql.py`가 FK 참조 순서로 테이블을 재배열하고 DDL을 만듭니다.
5. `render_review.py`가 빠진 객체·바뀐 이름·경고를 md로 만듭니다.
6. `cli.py`가 파일 이름과 리포트 모델을 결정합니다.

## 의존성

표준 라이브러리만 사용합니다. `sqlglot`·`SQLAlchemy`를 쓰지 않습니다.

이유는 dump 문법 때문입니다. `pg_dump`의 `ALTER TABLE ONLY ... ADD CONSTRAINT`와 MySQL의 조건부 주석 `/*!40101 ... */`는 표준 파서가 그대로 받아들이지 않는 경우가 있습니다. 필요한 문법만 직접 인식하고, 모르는 문장은 `warnings`에 남기는 쪽이 결과를 예측하기 쉽습니다.

## 확장 지점

- 새 dump 문법: `parse.py`의 `parse_statement`에 분기를 추가합니다.
- 새 DB 방언: `model.py`의 타입 정리와 `parse.py`의 노이즈 목록을 추가합니다.
- 출력 스타일: `render_sql.py`의 `render_table`·`align_body`를 고칩니다.
- 검토 md 구성: `render_review.py`
- 리포트 모델 필드: `cli.py`의 `build_model`

## 주의

- `render_sql.py`는 파싱 결과의 테이블 dict를 직접 고칩니다(`rendered` 플래그). 같은 결과로 두 번 렌더링하면 플래그가 남으므로, 렌더링은 한 번만 합니다.
