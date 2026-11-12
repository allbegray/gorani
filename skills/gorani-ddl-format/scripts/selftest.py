#!/usr/bin/env python3
"""gorani-ddl-format 회귀 검증.

실제 DB가 없어도 돌릴 수 있는 항목만 확인한다. DB 실행 검증은 SKILL.md의
절차대로 빈 DB에 결과 DDL을 넣어 확인한다.

    python3 skills/gorani-ddl-format/scripts/selftest.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ddl_format.cli import main
from ddl_format.parse import detect_dialect, parse_dump
from ddl_format.render_sql import Options, render
from ddl_format.tokenizer import split_statements

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SAMPLES = ROOT / "samples" / "ddl-format"

passed = 0
failed = []


def check(name, condition, detail=""):
    global passed
    if condition:
        passed += 1
    else:
        failed.append(f"{name}: {detail}")


def test_tokenizer():
    text = """
CREATE TABLE a (x text DEFAULT 'a;b');
CREATE TABLE b (y int);  -- 주석; 여기도
/* 블록; 주석 */
INSERT INTO a VALUES ('it''s; ok');
"""
    statements = split_statements(text)
    check("tokenizer 문자열 안 세미콜론", len(statements) == 3, f"{len(statements)}개")


def test_dialect_detection():
    pg = (SAMPLES / "postgres-dump.sql").read_text(encoding="utf-8")
    my = (SAMPLES / "mysql-dump.sql").read_text(encoding="utf-8")
    check("postgres 판별", detect_dialect(pg) == "postgres", detect_dialect(pg))
    check("mysql 판별", detect_dialect(my) == "mysql", detect_dialect(my))


def test_postgres():
    text = (SAMPLES / "postgres-dump.sql").read_text(encoding="utf-8")
    result = parse_dump(text, "auto")
    check("pg 경고 없음", not result.warnings, result.warnings)
    check("pg 테이블 4개", len(result.tables) == 4, len(result.tables))
    check("pg 컬럼 19개", sum(len(t["columns"]) for t in result.tables.values()) == 19)

    users = result.tables["public.users"]
    check("pg 복합 제약 흡수", bool(users["primary_key"]) and bool(users["foreign_keys"]))
    check("pg UNIQUE 1개", len(users["uniques"]) == 1, users["uniques"])
    check("pg CHECK 1개", len(users["checks"]) == 1, users["checks"])

    enums = [item for item in result.types if isinstance(item, dict)]
    check("pg ENUM 3값", enums and enums[0]["values"] == ["active", "blocked", "pending"], enums)

    ddl = render(result, Options(dialect="postgres", strip_schema="public"))
    check("pg FK가 테이블 안", "REFERENCES teams (id)" in ddl)
    check("pg ALTER TABLE 없음", "ALTER TABLE" not in ddl)
    check("pg COMMENT ON 있음", "COMMENT ON TABLE users" in ddl)
    check("pg COPY 없음", "COPY " not in ddl)
    check("pg bigserial", "bigserial" in ddl)
    check("pg varchar 별칭", "character varying" not in ddl)
    check("pg 캐스트 제거", "::" not in ddl)
    check("pg now() 공백 없음", "now ()" not in ddl)
    check("pg dump 이름 정리", "users_pkey" not in ddl and "users_email_key" not in ddl)
    check("pg FK 순서", ddl.index("CREATE TABLE teams") < ddl.index("CREATE TABLE users"))
    check("pg 하위 참조 순서", ddl.index("CREATE TABLE users") < ddl.index("CREATE TABLE projects"))
    check("pg partial index 유지", "WHERE team_id > 0" in ddl)
    check("pg 표현식 인덱스 정리", "lower(email)" in ddl and "::text" not in ddl)
    check("pg 타입 정렬", ddl.count("\n    ") > 15)
    check_index_grouping(ddl, "users", ["idx_users_lower_email", "idx_users_team", "uq_users_name_team"])
    return result


def check_index_grouping(ddl, table, index_names):
    """인덱스가 자기 테이블 다음, 다음 테이블 앞 구간에 있는지 확인한다."""
    positions = []
    for line in ddl.splitlines():
        if line.startswith("CREATE TABLE "):
            positions.append((line.split("(")[0].replace("CREATE TABLE", "").strip(), ddl.index(line)))
    for position, (name, _) in enumerate(positions):
        if name != table:
            continue
        start = position + 1
        end = positions[start][1] if start < len(positions) else len(ddl)
        section = ddl[positions[position][1] : end]
        for index_name in index_names:
            check(f"인덱스 {index_name}가 {table} 구간에 있음", index_name in section)


def test_mysql():
    text = (SAMPLES / "mysql-dump.sql").read_text(encoding="utf-8")
    result = parse_dump(text, "auto")
    check("mysql 경고 없음", not result.warnings, result.warnings)
    check("mysql 테이블 2개", len(result.tables) == 2, len(result.tables))
    users = result.tables["users"]
    check("mysql 인덱스 이름", users["indexes"][0]["name"] == "idx_users_team", users["indexes"])

    ddl = render(result, Options(dialect="mysql"))
    check("mysql ENGINE", "ENGINE=InnoDB" in ddl)
    check("mysql CHARSET", "DEFAULT CHARSET=utf8mb4" in ddl)
    check("mysql AUTO_INCREMENT", "AUTO_INCREMENT" in ddl)
    check("mysql 한글 주석 보존", "COMMENT '팀 이름'" in ddl)
    check("mysql KEY 인라인", "KEY idx_users_team (team_id)" in ddl or "KEY        idx_users_team" in ddl)
    check("mysql FK 제약", "FOREIGN KEY (team_id) REFERENCES teams (id)" in ddl)
    check("mysql 백틱 중복 없음", "```" not in ddl)
    check("mysql SET 제거", "UNIQUE_CHECKS" not in ddl)


def test_edge_cases():
    sql = """
CREATE TABLE public."order" (
    id bigint NOT NULL,
    "user" bigint NOT NULL,
    code character varying(20) NOT NULL,
    CONSTRAINT order_pkey PRIMARY KEY (id)
);
CREATE TABLE public.order_item (
    id bigint NOT NULL,
    order_id bigint NOT NULL,
    CONSTRAINT order_item_pkey PRIMARY KEY (id),
    CONSTRAINT order_item_order_fkey FOREIGN KEY (order_id) REFERENCES public."order"(id) ON DELETE CASCADE
);
CREATE TABLE public.node (
    id bigint NOT NULL,
    parent_id bigint,
    CONSTRAINT node_pkey PRIMARY KEY (id),
    CONSTRAINT node_parent_fkey FOREIGN KEY (parent_id) REFERENCES public.node(id)
);
CREATE TABLE public.pair (
    a bigint NOT NULL,
    b integer NOT NULL,
    CONSTRAINT pair_pkey PRIMARY KEY (a, b),
    CONSTRAINT pair_a_b_key UNIQUE (a, b)
);
CREATE TABLE public.pair_ref (
    id bigint NOT NULL,
    a bigint NOT NULL,
    b integer NOT NULL,
    CONSTRAINT pair_ref_pkey PRIMARY KEY (id),
    CONSTRAINT pair_ref_a_b_fkey FOREIGN KEY (a, b) REFERENCES public.pair(a, b) ON UPDATE CASCADE
);
"""
    result = parse_dump(sql, "auto")
    check("edge 경고 없음", not result.warnings, result.warnings)
    ddl = render(result, Options(dialect="postgres", strip_schema="public"))
    check("edge 예약어 컬럼 인용", '"user"' in ddl and '"order"' in ddl)
    check("edge 자기 참조 FK", "REFERENCES node (id)" in ddl)
    check("edge 복합 PK 제약 줄", "CONSTRAINT pk_pair_a_b PRIMARY KEY (a, b)" in ddl)
    check("edge 복합 UNIQUE 제약 줄", "UNIQUE (a, b)" in ddl and "CONSTRAINT" in ddl)
    check("edge 복합 FK 줄", "FOREIGN KEY (a, b) REFERENCES pair (a, b)" in ddl)
    check("edge ON UPDATE 유지", "ON UPDATE CASCADE" in ddl)
    check("edge ON DELETE 유지", "ON DELETE CASCADE" in ddl)


def test_identity_and_defaults():
    sql = """
CREATE TABLE t (
    id bigint NOT NULL,
    alt bigint GENERATED ALWAYS AS IDENTITY,
    flag boolean DEFAULT false NOT NULL,
    created timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT t_pkey PRIMARY KEY (id)
);
"""
    result = parse_dump(sql, "auto")
    ddl = render(result, Options(dialect="postgres", strip_schema="public"))
    check("identity 유지", "GENERATED ALWAYS AS IDENTITY" in ddl)
    check("boolean default", "DEFAULT false NOT NULL" in ddl)
    check("timestamptz", "timestamptz DEFAULT now() NOT NULL" in ddl)


def test_noise_skip():
    sql = """
SET client_encoding = 'UTF8';
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE TABLE t (id bigint NOT NULL, CONSTRAINT t_pkey PRIMARY KEY (id));
ALTER TABLE ONLY t OWNER TO postgres;
GRANT SELECT ON t TO readonly;
CREATE VIEW v AS SELECT * FROM t;
CREATE FUNCTION f() RETURNS int AS $$ SELECT 1; $$ LANGUAGE sql;
"""
    result = parse_dump(sql, "auto")
    check("noise 테이블만 남음", len(result.tables) == 1, len(result.tables))
    check("noise 경고 없음", not result.warnings, result.warnings)


def test_cli():
    with tempfile.TemporaryDirectory() as directory:
        outdir = Path(directory)
        code = main(
            [
                "--input",
                str(SAMPLES / "postgres-dump.sql"),
                "--outdir",
                str(outdir),
                "--name",
                "t",
                "--formats",
                "sql,review",
                "--generated-at",
                "2026-11-12T00:00:00+09:00",
            ]
        )
        check("cli exit 0", code == 0, code)
        check("cli sql 생성", (outdir / "t.sql").exists())
        check("cli review 생성", (outdir / "t.review.md").exists())
        check("cli 생성 시각 고정", "2026-11-12T00:00:00+09:00" in (outdir / "t.review.md").read_text(encoding="utf-8"))

        model_path = outdir / "model.json"
        main(
            [
                "--input",
                str(SAMPLES / "postgres-dump.sql"),
                "--outdir",
                str(outdir),
                "--name",
                "t",
                "--formats",
                "sql",
                "--model-out",
                str(model_path),
            ]
        )
        model = json.loads(model_path.read_text(encoding="utf-8"))
        check("cli 모델 summary", model["summary"]["tables"] == 4, model["summary"])
        check("cli 모델 enums", model["enums"][0]["values"] == ["active", "blocked", "pending"])


def test_cli_errors():
    import contextlib
    import io

    with tempfile.TemporaryDirectory() as directory:
        outdir = Path(directory)
        junk = outdir / "junk.sql"
        junk.write_text("hello world\n", encoding="utf-8")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            try:
                main(["--input", str(junk), "--outdir", str(outdir)])
                code = 0
            except SystemExit as error:
                code = error.code
        check("cli junk 거부", code not in (0, None), code)

        warn = outdir / "warn.sql"
        warn.write_text(
            "CREATE TABLE t (id bigint);\nALTER TABLE t RENAME COLUMN id TO ident;\n", encoding="utf-8"
        )
        try:
            code = main(["--input", str(warn), "--outdir", str(outdir), "--name", "w", "--strict"])
        except SystemExit as error:
            code = error.code
        check("cli strict 경고 시 exit 1", code not in (0, None), code)


def main_test():
    test_tokenizer()
    test_dialect_detection()
    test_postgres()
    test_mysql()
    test_edge_cases()
    test_identity_and_defaults()
    test_noise_skip()
    test_cli()
    test_cli_errors()

    print(f"통과 {passed}개, 실패 {len(failed)}개")
    for item in failed:
        print(f"  FAIL {item}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main_test())
