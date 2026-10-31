#!/usr/bin/env python3
"""SQL DDL 또는 실제 DB에서 테이블 명세서(Markdown·Excel)를 만든다.

입력: SQL DDL 파일 또는 SQLAlchemy DB URL
출력: table-spec.md, table-spec.xlsx

DDL은 sqlglot으로, DB는 SQLAlchemy Inspector로 읽는다. 실제 DB 모드는
접속 시점의 스키마를 읽으며 스키마·데이터를 수정하지 않는다.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    sqlglot = None
    exp = None

DIALECTS = ["postgres", "mysql", "sqlite", "mssql", "oracle"]
OUTPUT_FORMATS = ("md", "xlsx", "html")
DEFAULT_FORMATS = "xlsx,md,html"
SYSTEM_TABLE_NAMES = {"msreplication_options", "sysdiagrams"}
SYSTEM_TABLE_PREFIXES = ("spt_", "trace_xe_")
SYSTEM_SCHEMAS = {"information_schema", "sys", "mysql", "performance_schema"}


def parse_args():
    parser = argparse.ArgumentParser(description="SQL DDL에서 테이블 명세서 생성")
    parser.add_argument(
        "--ddl",
        action="append",
        help="SQL 파일 또는 디렉터리. 여러 번 지정할 수 있음",
    )
    parser.add_argument(
        "--db-url",
        help="SQLAlchemy DB URL. 예: postgresql+psycopg://user:pass@host/db, mysql+pymysql://..., sqlite:///path",
    )
    parser.add_argument(
        "--schema",
        action="append",
        default=[],
        help="DB 모드에서 조회할 스키마. 여러 번 지정할 수 있음 (기본: DB 기본 스키마)",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="DB 모드에서 시스템 테이블도 포함",
    )
    parser.add_argument(
        "--dialect",
        default="auto",
        choices=["auto", *DIALECTS],
        help="SQL 방언 (기본: auto)",
    )
    parser.add_argument("--outdir", default="docs/db", help="출력 디렉터리")
    parser.add_argument("--name", default="table-spec", help="출력 파일 기본 이름")
    parser.add_argument("--project", default="", help="프로젝트명 (기본: 저장소 폴더명)")
    parser.add_argument(
        "--formats",
        default=DEFAULT_FORMATS,
        help=f"생성할 산출물: {','.join(OUTPUT_FORMATS)} (기본: {DEFAULT_FORMATS})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="파싱 경고가 있으면 종료 코드 1",
    )
    args = parser.parse_args()
    if not args.ddl and not args.db_url:
        parser.error("--ddl 또는 --db-url 중 하나를 지정하세요.")
    if args.ddl and args.db_url:
        parser.error("--ddl 과 --db-url 은 함께 쓸 수 없습니다.")
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    unknown = [item for item in formats if item not in OUTPUT_FORMATS]
    if unknown:
        parser.error(f"지원하지 않는 형식입니다: {', '.join(unknown)}")
    if not formats:
        parser.error("--formats 에 하나 이상의 형식을 지정하세요.")
    args.formats = set(formats)
    return args


def collect_files(paths):
    files = []
    seen = set()
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            candidates = sorted(
                item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".sql", ".ddl"}
            )
        elif path.is_file():
            candidates = [path]
        else:
            sys.exit(f"DDL 경로가 없습니다: {raw}")
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)
    if not files:
        sys.exit("SQL 파일을 찾지 못했습니다. --ddl 경로를 확인하세요.")
    return files


def parse_statements(text, dialect, path):
    candidates = DIALECTS if dialect == "auto" else [dialect]
    last_error = None
    for candidate in candidates:
        try:
            statements = sqlglot.parse(text, read=candidate)
            return [statement for statement in statements if statement is not None], candidate
        except Exception as error:  # sqlglot ParseError를 포함한 방언별 오류
            last_error = error
    raise SystemExit(f"SQL 파싱에 실패했습니다: {path} ({last_error})")


def literal_text(value):
    if value is None:
        return ""
    if isinstance(value, exp.Literal):
        return str(value.this)
    return str(value.sql())


def table_identity(value):
    if isinstance(value, exp.Schema):
        value = value.this
    if isinstance(value, exp.Table):
        return str(value.db or ""), str(value.name or "")
    if isinstance(value, exp.Column):
        return str(value.db or ""), str(value.name or "")
    return "", str(getattr(value, "name", "") or "")


def table_key(schema, name):
    return f"{schema}.{name}" if schema else name


def split_type(type_sql):
    text = (type_sql or "-").strip()
    match = re.match(r"^([^(]+?)(?:\((.*)\))?$", text)
    if not match:
        return text, ""
    return match.group(1).strip(), (match.group(2) or "").strip()


def parse_reference(reference):
    target = reference.this
    ref_schema = ""
    ref_table = ""
    ref_columns = []
    if isinstance(target, exp.Schema):
        ref_schema, ref_table = table_identity(target.this)
        ref_columns = [str(item.name) for item in target.expressions if getattr(item, "name", None)]
    elif isinstance(target, exp.Table):
        ref_schema, ref_table = table_identity(target)
    options = [str(option).upper() for option in (reference.args.get("options") or [])]
    on_delete = ""
    on_update = ""
    for option in options:
        if "ON DELETE" in option:
            on_delete = option.split("ON DELETE", 1)[1].strip()
        elif "ON UPDATE" in option:
            on_update = option.split("ON UPDATE", 1)[1].strip()
    return {
        "schema": ref_schema,
        "table": ref_table,
        "columns": ref_columns,
        "on_delete": on_delete,
        "on_update": on_update,
    }


def new_column(name, data_type, length="", nullable=True, default="", comment="", source=""):
    return {
        "name": name,
        "data_type": data_type or "-",
        "length": length,
        "nullable": nullable,
        "default": default,
        "primary_key": False,
        "unique": False,
        "references": False,
        "reference_info": None,
        "comment": comment,
        "auto_increment": False,
        "check": "",
        "source": source,
    }


def parse_column_def(column_def, dialect, source):
    name = str(column_def.name)
    kind = column_def.args.get("kind")
    type_sql = kind.sql(dialect=dialect) if kind is not None else "-"
    data_type, length = split_type(type_sql)
    column = new_column(name, data_type, length, source=source)
    for constraint in column_def.constraints or []:
        kind = constraint.kind
        if isinstance(kind, exp.NotNullColumnConstraint):
            column["nullable"] = False
        elif isinstance(kind, exp.PrimaryKeyColumnConstraint):
            column["primary_key"] = True
            column["nullable"] = False
        elif isinstance(kind, exp.UniqueColumnConstraint):
            column["unique"] = True
        elif isinstance(kind, exp.DefaultColumnConstraint):
            column["default"] = kind.this.sql(dialect=dialect) if kind.this is not None else ""
        elif isinstance(kind, exp.Reference):
            column["reference_info"] = parse_reference(kind)
        elif isinstance(kind, exp.CommentColumnConstraint):
            column["comment"] = literal_text(kind.this)
        elif isinstance(kind, exp.AutoIncrementColumnConstraint):
            column["auto_increment"] = True
        elif isinstance(kind, exp.CheckColumnConstraint):
            column["check"] = kind.this.sql(dialect=dialect) if kind.this is not None else ""
    return column


def column_names(item):
    if isinstance(item, exp.PrimaryKey):
        return [str(value.name) for value in item.expressions if getattr(value, "name", None)]
    if isinstance(item, exp.UniqueColumnConstraint):
        schema = item.this
        if isinstance(schema, exp.Schema):
            return [str(value.name) for value in schema.expressions if getattr(value, "name", None)]
        return [str(schema.name)] if getattr(schema, "name", None) else []
    if isinstance(item, exp.ForeignKey):
        return [str(value.name) for value in item.expressions if getattr(value, "name", None)]
    if isinstance(item, exp.IndexColumnConstraint):
        return [str(value.name) for value in item.expressions if getattr(value, "name", None)]
    if isinstance(item, exp.Schema):
        return [str(value.name) for value in item.expressions if getattr(value, "name", None)]
    if hasattr(item, "expressions"):
        return [str(value.name) for value in item.expressions if getattr(value, "name", None)]
    return []


def mark_columns(table, columns, field, value=True):
    names = set(columns)
    for column in table["columns"]:
        if column["name"] in names:
            column[field] = value


def add_foreign_key(table, name, columns, reference):
    if not columns or not reference.get("table"):
        return
    if not name:
        name = f"fk_{table['name']}_{'_'.join(columns)}"
    key = (name, tuple(columns), reference.get("table"), tuple(reference.get("columns") or []))
    existing = {
        (item["name"], tuple(item["columns"]), item["ref_table"], tuple(item["ref_columns"]))
        for item in table["foreign_keys"]
    }
    if key in existing:
        return
    table["foreign_keys"].append(
        {
            "name": name or "-",
            "columns": columns,
            "ref_schema": reference.get("schema", ""),
            "ref_table": reference["table"],
            "ref_columns": reference.get("columns") or [],
            "on_delete": reference.get("on_delete", ""),
            "on_update": reference.get("on_update", ""),
        }
    )
    mark_columns(table, columns, "references", True)


def add_unique(table, name, columns):
    if not columns:
        return
    key = (name or "-", tuple(columns))
    if any((item["name"], tuple(item["columns"])) == key for item in table["uniques"]):
        return
    table["uniques"].append({"name": name or "-", "columns": columns})
    if len(columns) == 1:
        mark_columns(table, columns, "unique", True)


def add_index(table, name, columns, unique=False, source=""):
    if not columns:
        return
    key = (name or "-", tuple(columns), bool(unique))
    if any(
        (item["name"], tuple(item["columns"]), item["unique"]) == key for item in table["indexes"]
    ):
        return
    table["indexes"].append(
        {"name": name or "-", "columns": columns, "unique": bool(unique), "source": source}
    )


def apply_constraint_item(table, item, name="", dialect="postgres"):
    if isinstance(item, exp.PrimaryKey):
        columns = column_names(item)
        table["primary_key"] = columns
        mark_columns(table, columns, "primary_key", True)
        mark_columns(table, columns, "nullable", False)
    elif isinstance(item, exp.UniqueColumnConstraint):
        columns = column_names(item)
        constraint_name = name
        if not constraint_name and isinstance(item.this, exp.Schema) and item.this.this is not None:
            constraint_name = str(item.this.this.name or "")
        add_unique(table, constraint_name, columns)
        add_index(table, constraint_name or "-", columns, unique=True, source="unique constraint")
    elif isinstance(item, exp.ForeignKey):
        columns = column_names(item)
        add_foreign_key(table, name, columns, parse_reference(item.args.get("reference")))
    elif isinstance(item, exp.IndexColumnConstraint):
        columns = column_names(item)
        index_name = str(item.name or "") if getattr(item, "name", None) else ""
        add_index(table, index_name, columns, unique=False, source="inline index")
    elif isinstance(item, exp.CheckColumnConstraint):
        return


def apply_table_constraint(table, constraint, dialect):
    name = str(constraint.name or "")
    for item in constraint.expressions:
        apply_constraint_item(table, item, name=name, dialect=dialect)


def new_table(schema, name, source):
    return {
        "schema": schema,
        "name": name,
        "description": "",
        "columns": [],
        "primary_key": [],
        "foreign_keys": [],
        "uniques": [],
        "indexes": [],
        "source_files": [source] if source else [],
    }


def parse_create_table(statement, dialect, source, tables, warnings):
    schema_node = statement.this
    if not isinstance(schema_node, exp.Schema):
        warnings.append(f"CREATE TABLE 구조를 해석하지 못했습니다: {statement}")
        return
    table_expr = schema_node.this
    schema, name = table_identity(table_expr)
    if not name:
        warnings.append(f"CREATE TABLE 이름을 찾지 못했습니다: {statement}")
        return
    key = table_key(schema, name)
    if key in tables and tables[key]["columns"]:
        warnings.append(f"테이블이 여러 번 정의됐습니다. 마지막 정의를 사용합니다: {key}")
    table = new_table(schema, name, source)
    properties = statement.args.get("properties")
    if properties is not None:
        for prop in properties.expressions:
            if isinstance(prop, exp.SchemaCommentProperty):
                table["description"] = literal_text(prop.this)
    for item in schema_node.expressions:
        if isinstance(item, exp.ColumnDef):
            table["columns"].append(parse_column_def(item, dialect, source))
        elif isinstance(item, exp.Constraint):
            apply_table_constraint(table, item, dialect)
        else:
            apply_constraint_item(table, item, dialect=dialect)
    if not table["columns"]:
        warnings.append(f"컬럼을 찾지 못했습니다: {key}")
    tables[key] = table


def parse_create_index(statement, dialect, source, tables, warnings):
    index = statement.this
    if not isinstance(index, exp.Index):
        warnings.append(f"CREATE INDEX 구조를 해석하지 못했습니다: {statement}")
        return
    table_expr = index.args.get("table")
    schema, table_name = table_identity(table_expr) if table_expr is not None else ("", "")
    key = table_key(schema, table_name)
    table = tables.get(key)
    if table is None:
        warnings.append(f"인덱스 대상 테이블을 찾지 못했습니다: {key}")
        return
    params = index.args.get("params")
    columns = []
    if params is not None:
        for value in params.args.get("columns") or []:
            target = value.this if isinstance(value, exp.Ordered) else value
            if isinstance(target, exp.Column):
                columns.append(str(target.name))
            elif getattr(target, "name", None):
                columns.append(str(target.name))
            else:
                columns.append(str(target.sql(dialect=dialect)))
    name = str(index.name or "")
    if source and source not in table["source_files"]:
        table["source_files"].append(source)
    add_index(table, name, columns, unique=bool(statement.args.get("unique")), source=source)


def parse_comment(statement, tables, warnings, source=""):
    kind = str(statement.args.get("kind") or "").upper()
    target = statement.args.get("this")
    text = literal_text(statement.args.get("expression"))
    if kind == "TABLE":
        schema, name = table_identity(target)
        table = tables.get(table_key(schema, name))
        if table is None:
            warnings.append(f"테이블 설명 대상이 없습니다: {table_key(schema, name)}")
            return
        table["description"] = text
        if source and source not in table["source_files"]:
            table["source_files"].append(source)
    elif kind == "COLUMN" and isinstance(target, exp.Column):
        schema = str(target.db or "")
        table_name = str(target.table or "")
        table = tables.get(table_key(schema, table_name))
        if table is None:
            warnings.append(f"컬럼 설명 대상 테이블이 없습니다: {table_key(schema, table_name)}")
            return
        for column in table["columns"]:
            if column["name"] == str(target.name):
                column["comment"] = text
                if source and source not in table["source_files"]:
                    table["source_files"].append(source)
                return
        warnings.append(f"컬럼 설명 대상이 없습니다: {table_key(schema, table_name)}.{target.name}")
    else:
        warnings.append(f"COMMENT 대상을 해석하지 못했습니다: {statement}")


def find_column(table, name):
    for column in table["columns"]:
        if column["name"] == name:
            return column
    return None


def rename_column(table, old, new):
    column = find_column(table, old)
    if column is None:
        return
    column["name"] = new
    for key in ("primary_key",):
        table[key] = [new if value == old else value for value in table[key]]
    for foreign_key in table["foreign_keys"]:
        foreign_key["columns"] = [new if value == old else value for value in foreign_key["columns"]]
    for unique in table["uniques"]:
        unique["columns"] = [new if value == old else value for value in unique["columns"]]
    for index in table["indexes"]:
        index["columns"] = [new if value == old else value for value in index["columns"]]


def parse_alter(statement, dialect, source, tables, warnings):
    schema, name = table_identity(statement.this)
    key = table_key(schema, name)
    table = tables.get(key)
    if table is None:
        warnings.append(f"ALTER TABLE 대상이 없습니다: {key}")
        return
    if source and source not in table["source_files"]:
        table["source_files"].append(source)
    for action in statement.args.get("actions") or []:
        if isinstance(action, exp.ColumnDef):
            column = parse_column_def(action, dialect, source)
            existing = find_column(table, column["name"])
            if existing is not None:
                table["columns"][table["columns"].index(existing)] = column
            else:
                table["columns"].append(column)
        elif isinstance(action, exp.Drop):
            drop_kind = str(action.args.get("kind") or "").upper()
            targets = action.args.get("tables") or []
            names = [str(target.name) for target in targets if getattr(target, "name", None)]
            if drop_kind == "COLUMN":
                table["columns"] = [column for column in table["columns"] if column["name"] not in names]
                table["primary_key"] = [value for value in table["primary_key"] if value not in names]
                for foreign_key in table["foreign_keys"]:
                    foreign_key["columns"] = [value for value in foreign_key["columns"] if value not in names]
            elif drop_kind == "CONSTRAINT":
                table["foreign_keys"] = [item for item in table["foreign_keys"] if item["name"] not in names]
                table["uniques"] = [item for item in table["uniques"] if item["name"] not in names]
            elif drop_kind == "INDEX":
                table["indexes"] = [item for item in table["indexes"] if item["name"] not in names]
            else:
                warnings.append(f"지원하지 않는 ALTER DROP입니다: {action}")
        elif isinstance(action, exp.RenameColumn):
            target = action.args.get("this")
            destination = action.args.get("to")
            rename_column(
                table,
                str(target.name) if target is not None else "",
                str(destination.name) if destination is not None else "",
            )
        elif isinstance(action, exp.AlterColumn):
            column = find_column(table, str(action.this.name))
            if column is None:
                warnings.append(f"ALTER COLUMN 대상이 없습니다: {key}.{action.this.name}")
                continue
            if action.args.get("dtype") is not None:
                type_sql = action.args["dtype"].sql(dialect=dialect)
                column["data_type"], column["length"] = split_type(type_sql)
            if action.args.get("allow_null") is False:
                column["nullable"] = False
            elif action.args.get("allow_null") is True:
                column["nullable"] = True
            if action.args.get("default") is not None:
                column["default"] = action.args["default"].sql(dialect=dialect)
        elif isinstance(action, exp.AddConstraint):
            name_match = re.search(
                r"\bCONSTRAINT\s+[`\"]?([\w.]+)[`\"]?",
                action.sql(dialect=dialect),
                re.I,
            )
            constraint_name = name_match.group(1) if name_match else ""
            for item in action.expressions:
                if isinstance(item, exp.Constraint):
                    apply_table_constraint(table, item, dialect)
                else:
                    apply_constraint_item(table, item, name=constraint_name, dialect=dialect)
        elif isinstance(action, exp.AlterRename):
            new_schema, new_name = table_identity(action.this)
            if new_name:
                new_key = table_key(new_schema or schema, new_name)
                old_key = key
                table["name"] = new_name
                table["schema"] = new_schema or schema
                tables[new_key] = tables.pop(old_key)
                key = new_key
                for other in tables.values():
                    for foreign_key in other["foreign_keys"]:
                        if foreign_key["ref_table"] == name and foreign_key["ref_schema"] == schema:
                            foreign_key["ref_table"] = new_name
                            foreign_key["ref_schema"] = new_schema or schema
        else:
            warnings.append(f"지원하지 않는 ALTER 동작입니다: {action}")


def parse_drop(statement, tables, warnings):
    drop_kind = str(statement.args.get("kind") or "").upper()
    if drop_kind != "TABLE":
        warnings.append(f"지원하지 않는 DROP입니다: {statement}")
        return
    targets = statement.args.get("this") or []
    if not isinstance(targets, list):
        targets = [targets]
    for target in targets:
        schema, name = table_identity(target)
        key = table_key(schema, name)
        if key in tables:
            del tables[key]
        else:
            warnings.append(f"DROP TABLE 대상이 없습니다: {key}")


def parse_ddl(files, dialect):
    if sqlglot is None:
        sys.exit(
            "DDL 모드에는 sqlglot이 필요합니다. 스킬의 도구 설치 원칙에 따라 설치한 뒤 다시 시도하세요. "
            "예: python3 -m pip install --user sqlglot"
        )
    tables = {}
    warnings = []
    parsed_dialects = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            warnings.append(f"빈 SQL 파일입니다: {path}")
            continue
        statements, used_dialect = parse_statements(text, dialect, path)
        parsed_dialects.append(used_dialect)
        for statement in statements:
            if isinstance(statement, exp.Create):
                kind = str(statement.args.get("kind") or "").upper()
                if kind == "TABLE":
                    parse_create_table(statement, used_dialect, str(path), tables, warnings)
                elif kind == "INDEX":
                    parse_create_index(statement, used_dialect, str(path), tables, warnings)
                elif kind in {"SCHEMA", "EXTENSION", "TYPE", "SEQUENCE", "VIEW", "FUNCTION", "TRIGGER", "PROCEDURE"}:
                    continue
                else:
                    warnings.append(f"지원하지 않는 CREATE입니다: {statement}")
            elif isinstance(statement, exp.Alter):
                parse_alter(statement, used_dialect, str(path), tables, warnings)
            elif isinstance(statement, exp.Comment):
                parse_comment(statement, tables, warnings, str(path))
            elif isinstance(statement, exp.Drop):
                parse_drop(statement, tables, warnings)
            elif isinstance(statement, exp.Transaction):
                continue
            else:
                warnings.append(f"무시한 SQL 문입니다: {statement}")
    return tables, warnings, parsed_dialects


def redact_url(url):
    try:
        from sqlalchemy.engine import make_url

        return make_url(url).render_as_string(hide_password=True)
    except Exception:
        return re.sub(r"(://[^:/@]+:)[^@]+@", r"\1***@", str(url))


def is_system_table(schema, name, dialect=""):
    lower_name = str(name or "").lower()
    lower_schema = str(schema or "").lower()
    if lower_schema in SYSTEM_SCHEMAS:
        return True
    if dialect == "mssql":
        return lower_name in SYSTEM_TABLE_NAMES or lower_name.startswith(SYSTEM_TABLE_PREFIXES)
    return False


def introspect_db(db_url, schemas, warnings, include_system=False):
    try:
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.exc import SQLAlchemyError
    except ImportError:
        sys.exit(
            "DB 모드에는 SQLAlchemy가 필요합니다. 스킬의 도구 설치 원칙에 따라 설치한 뒤 다시 시도하세요. "
            "예: python3 -m pip install --user sqlalchemy psycopg[binary]  # PostgreSQL"
        )
    redacted = redact_url(db_url)
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            inspector = inspect(connection)
            dialect = engine.dialect.name
            default_schema = inspector.default_schema_name
            target_schemas = schemas or [default_schema]
            tables = {}
            for schema in target_schemas:
                try:
                    names = inspector.get_table_names(schema=schema)
                except Exception as error:
                    warnings.append(f"테이블 목록을 읽지 못했습니다: schema={schema} ({error})")
                    continue
                for name in sorted(names):
                    if not include_system and is_system_table(schema, name, dialect):
                        continue
                    table = new_table(schema or "", name, "")
                    try:
                        comment = inspector.get_table_comment(name, schema=schema)
                        table["description"] = (comment or {}).get("text") or ""
                    except Exception:
                        pass
                    try:
                        columns = inspector.get_columns(name, schema=schema)
                    except Exception as error:
                        warnings.append(f"컬럼을 읽지 못했습니다: {table_key(schema or '', name)} ({error})")
                        continue
                    for raw in columns:
                        type_sql = re.sub(
                            r"\s+COLLATE\s+.*$",
                            "",
                            str(raw.get("type", "-")),
                            flags=re.I,
                        )
                        data_type, length = split_type(type_sql)
                        column = new_column(
                            str(raw.get("name", "")),
                            data_type,
                            length,
                            nullable=bool(raw.get("nullable", True)),
                            default="" if raw.get("default") is None else str(raw.get("default")),
                            comment=str(raw.get("comment") or ""),
                        )
                        if raw.get("autoincrement") is True:
                            column["auto_increment"] = True
                        table["columns"].append(column)
                    try:
                        primary_key = inspector.get_pk_constraint(name, schema=schema)
                        table["primary_key"] = [
                            str(value) for value in (primary_key or {}).get("constrained_columns") or []
                        ]
                    except Exception:
                        pass
                    try:
                        foreign_keys = inspector.get_foreign_keys(name, schema=schema)
                    except Exception:
                        foreign_keys = []
                    for foreign_key in foreign_keys:
                        options = foreign_key.get("options") or {}
                        add_foreign_key(
                            table,
                            str(foreign_key.get("name") or ""),
                            [str(value) for value in foreign_key.get("constrained_columns") or []],
                            {
                                "schema": str(foreign_key.get("referred_schema") or schema or ""),
                                "table": str(foreign_key.get("referred_table") or ""),
                                "columns": [str(value) for value in foreign_key.get("referred_columns") or []],
                                "on_delete": str(options.get("ondelete") or ""),
                                "on_update": str(options.get("onupdate") or ""),
                            },
                        )
                    try:
                        indexes = inspector.get_indexes(name, schema=schema)
                    except Exception:
                        indexes = []
                    for index in indexes:
                        add_index(
                            table,
                            str(index.get("name") or ""),
                            [str(value) for value in index.get("column_names") or []],
                            unique=bool(index.get("unique")),
                            source="database",
                        )
                    try:
                        unique_constraints = inspector.get_unique_constraints(name, schema=schema)
                    except Exception:
                        unique_constraints = []
                    for unique in unique_constraints:
                        add_unique(
                            table,
                            str(unique.get("name") or ""),
                            [str(value) for value in unique.get("column_names") or []],
                        )
                    tables[table_key(schema or "", name)] = table
        engine.dispose()
        return tables, warnings, [dialect], f"DB {redacted}"
    except ModuleNotFoundError as error:
        sys.exit(
            f"DB 드라이버를 찾지 못했습니다: {error}. "
            "PostgreSQL은 psycopg[binary], MySQL은 pymysql 설치가 필요합니다."
        )
    except SQLAlchemyError as error:
        sys.exit(f"DB 연결 또는 조회에 실패했습니다: {redacted} ({error})")


def finalize_tables(tables):
    for table in tables.values():
        if not table["primary_key"]:
            table["primary_key"] = [column["name"] for column in table["columns"] if column["primary_key"]]
        else:
            mark_columns(table, table["primary_key"], "primary_key", True)
            mark_columns(table, table["primary_key"], "nullable", False)
        for column in table["columns"]:
            reference = column.get("reference_info")
            if reference:
                add_foreign_key(
                    table,
                    "",
                    [column["name"]],
                    {
                        "schema": reference.get("schema", ""),
                        "table": reference.get("table", ""),
                        "columns": reference.get("columns", []),
                        "on_delete": reference.get("on_delete", ""),
                        "on_update": reference.get("on_update", ""),
                    },
                )
        for foreign_key in table["foreign_keys"]:
            for column in table["columns"]:
                if column["name"] in foreign_key["columns"]:
                    column["references"] = True
        for column in table["columns"]:
            if column["unique"] and not any(
                index["unique"] and index["columns"] == [column["name"]] for index in table["indexes"]
            ):
                add_index(
                    table,
                    f"uq_{table['name']}_{column['name']}",
                    [column["name"]],
                    unique=True,
                    source="column unique",
                )
        for column in table["columns"]:
            notes = []
            if column["auto_increment"]:
                notes.append("AUTO_INCREMENT")
            if column["check"]:
                notes.append(f"CHECK {column['check']}")
            column["note"] = " / ".join(notes)
    return dict(sorted(tables.items()))


def md_cell(value):
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ") or "-"


def table_label(table):
    return f"{table['schema']}.{table['name']}" if table["schema"] else table["name"]


def build_markdown(data, tables):
    lines = [
        "# 테이블 명세서",
        "",
        f"- 프로젝트: {data['project'] or '-'}",
        f"- 생성 시각: {data['generated_at']}",
        f"- SQL 방언: {', '.join(data['dialects']) or '-'}",
        f"- 원본: {data.get('source_label', '-')}",
        f"- 테이블: {len(tables)}",
        f"- 컬럼: {data['column_count']}",
        f"- 관계: {data['fk_count']}",
        f"- 인덱스: {data['index_count']}",
        "",
        "> 이 문서는 DB에서 조회한 스키마를 기준으로 생성했습니다. 조회 시점 이후 변경될 수 있습니다."
        if data.get("source") == "database"
        else "> 이 문서는 SQL DDL을 기준으로 생성했습니다. 런타임 DB 상태와 다를 수 있습니다.",
        "",
        "## 테이블 목록",
        "",
        "| No | 스키마 | 테이블 | 설명 | 컬럼 | PK | FK | 인덱스 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, table in enumerate(tables.values(), start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(table["schema"] or "-"),
                    md_cell(table["name"]),
                    md_cell(table["description"] or "-"),
                    str(len(table["columns"])),
                    md_cell(", ".join(table["primary_key"]) or "-"),
                    str(len(table["foreign_keys"])),
                    str(len(table["indexes"])),
                ]
            )
            + " |"
        )
    for table in tables.values():
        lines += [
            "",
            f"## {table['name']}" + (f" — {table['description']}" if table["description"] else ""),
            "",
            f"- 스키마: {table['schema'] or '-'}",
        ]
        if table["source_files"]:
            lines.append(f"- 원본: {', '.join(table['source_files'])}")
        lines += [
            "",
            "| No | 컬럼 | 데이터 타입 | 길이 | PK | FK | UNIQUE | NOT NULL | DEFAULT | 설명 | 비고 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for index, column in enumerate(table["columns"], start=1):
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(index),
                        md_cell(column["name"]),
                        md_cell(column["data_type"]),
                        md_cell(column["length"] or "-"),
                        "Y" if column["primary_key"] else "-",
                        "Y" if column["references"] else "-",
                        "Y" if column["unique"] else "-",
                        "Y" if not column["nullable"] else "-",
                        md_cell(column["default"] or "-"),
                        md_cell(column["comment"] or "-"),
                        md_cell(column["note"] or "-"),
                    ]
                )
                + " |"
            )
        if table["foreign_keys"]:
            lines += [
                "",
                "### 관계",
                "",
                "| FK | 컬럼 | 참조 테이블 | 참조 컬럼 | ON DELETE | ON UPDATE |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
            for foreign_key in table["foreign_keys"]:
                ref_table = (
                    f"{foreign_key['ref_schema']}.{foreign_key['ref_table']}"
                    if foreign_key["ref_schema"]
                    else foreign_key["ref_table"]
                )
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            md_cell(foreign_key["name"]),
                            md_cell(", ".join(foreign_key["columns"]) or "-"),
                            md_cell(ref_table or "-"),
                            md_cell(", ".join(foreign_key["ref_columns"]) or "-"),
                            md_cell(foreign_key["on_delete"] or "-"),
                            md_cell(foreign_key["on_update"] or "-"),
                        ]
                    )
                    + " |"
                )
        if table["indexes"]:
            lines += [
                "",
                "### 인덱스",
                "",
                "| 인덱스 | UNIQUE | 컬럼 |",
                "| --- | --- | --- |",
            ]
            for index in table["indexes"]:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            md_cell(index["name"]),
                            "Y" if index["unique"] else "-",
                            md_cell(", ".join(index["columns"]) or "-"),
                        ]
                    )
                    + " |"
                )
    if data["warnings"]:
        lines += ["", "## 파싱 메모", ""]
        for warning in data["warnings"]:
            lines.append(f"- {warning}")
    return "\n".join(lines).rstrip() + "\n"


def build_html(data, tables):
    project = str(data.get("project", ""))
    generated_at = str(data.get("generated_at", ""))
    source_label = str(data.get("source_label", ""))
    dialect = ", ".join(data.get("dialects") or [])
    document_title = f"테이블 명세서 — {project}" if project else "테이블 명세서"

    def value(raw):
        text = "" if raw is None else str(raw)
        return html.escape(text or "-")

    def flag(active, label="Y"):
        if active:
            return f'<span class="flag yes">{html.escape(label)}</span>'
        return '<span class="flag">-</span>'

    stats = [
        ("테이블", len(tables)),
        ("컬럼", data["column_count"]),
        ("관계", data["fk_count"]),
        ("인덱스", data["index_count"]),
    ]
    css = """
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #17181c;
  --muted: #5c6270;
  --line: #e2e5ea;
  --panel: #f6f7f9;
  --accent: #1f5fbf;
  --code: #f3f4f6;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111216;
    --fg: #e8eaee;
    --muted: #9aa1ae;
    --line: #2a2d35;
    --panel: #181a20;
    --accent: #9db8e8;
    --code: #1a1c22;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif; }
main, header, footer { max-width: 78rem; margin: 0 auto; padding: 0 1.25rem; }
header { padding-top: 2.5rem; padding-bottom: .5rem; }
h1 { font-size: 1.8rem; line-height: 1.2; margin: 0 0 .4rem; letter-spacing: -.02em; }
h2 { font-size: 1.15rem; margin: 0; }
h3 { font-size: .95rem; margin: 0 0 .5rem; }
p { margin: .35rem 0; }
.eyebrow { color: var(--accent); font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.meta { color: var(--muted); font-size: .875rem; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: .65rem; margin: 1.5rem 0 1rem; }
.stat { padding: .75rem .9rem; background: var(--panel); border: 1px solid var(--line); border-radius: .6rem; }
.stat strong { display: block; font-size: 1.25rem; line-height: 1.2; }
.stat span { color: var(--muted); font-size: .78rem; }
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: .75rem; margin: 1.2rem 0 .8rem; padding: .85rem 1rem; background: var(--panel); border: 1px solid var(--line); border-radius: .7rem; }
.controls label { font-weight: 600; font-size: .875rem; }
.controls input { flex: 1 1 16rem; min-width: 0; padding: .55rem .75rem; color: var(--fg); background: var(--bg); border: 1px solid var(--line); border-radius: .45rem; font: inherit; }
.controls input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.count { margin: 0; color: var(--muted); font-size: .8125rem; }
.toc { margin: .8rem 0 1.5rem; }
.toc ul { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0; padding: 0; list-style: none; }
.toc a { display: inline-flex; padding: .28rem .6rem; color: var(--fg); background: var(--panel); border: 1px solid var(--line); border-radius: 999px; font-size: .8rem; text-decoration: none; }
.toc a:hover { border-color: var(--accent); }
.overview { margin: 1.5rem 0 2rem; }
.table-card { padding: 1.5rem 0; border-top: 1px solid var(--line); scroll-margin-top: 1rem; }
.table-card h2 { display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem; }
.table-card h2 .desc { color: var(--muted); font-size: .9rem; font-weight: 400; }
.table-card .meta { margin-bottom: .75rem; }
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: .5rem; }
table { width: 100%; border-collapse: collapse; font-size: .84rem; }
th, td { padding: .5rem .6rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
tr:last-child td { border-bottom: 0; }
th { background: var(--panel); color: var(--muted); font-size: .76rem; font-weight: 600; white-space: nowrap; }
tbody tr:nth-child(even) td { background: color-mix(in srgb, var(--panel) 55%, transparent); }
.flag { color: var(--muted); }
.flag.yes { color: var(--accent); font-weight: 700; }
.subsection { margin-top: 1rem; }
.warnings { margin: 1.5rem 0; padding: 1rem; border: 1px dashed var(--line); border-radius: .6rem; }
.warnings h2 { font-size: 1rem; margin-bottom: .4rem; }
.warnings ul { margin: .25rem 0 0; padding-left: 1.2rem; color: var(--muted); font-size: .875rem; }
footer { padding-top: 2rem; padding-bottom: 2.5rem; color: var(--muted); font-size: .8125rem; border-top: 1px solid var(--line); }
[hidden] { display: none !important; }
@media print {
  .controls, .toc, footer { display: none; }
  .table-card { break-inside: avoid-page; }
  body { font-size: 10.5pt; }
}
""".strip()
    javascript = """
(function () {
  var input = document.getElementById("search");
  if (!input) return;
  var count = document.getElementById("result-count");
  var cards = Array.prototype.slice.call(document.querySelectorAll(".table-card"));
  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  var initial = count ? count.textContent : "";
  function apply() {
    var query = (input.value || "").trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {
      var match = !query || (card.getAttribute("data-search") || "").indexOf(query) !== -1;
      card.hidden = !match;
      if (match) shown += 1;
    });
    links.forEach(function (link) {
      var target = document.querySelector(link.getAttribute("href"));
      link.parentNode.hidden = !!(target && target.hidden);
    });
    if (count) {
      count.textContent = query ? shown + " / " + cards.length + " tables" : initial;
    }
  }
  input.addEventListener("input", apply);
})();
""".strip()
    parts = [
        "<!doctype html>",
        '<html lang="ko">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'\">",
        f"<title>{html.escape(document_title)}</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        "<header>",
        '<p class="eyebrow">Database specification</p>',
        f"<h1>{html.escape(document_title)}</h1>",
        f'<p class="meta">{html.escape(project or "-")} · {html.escape(generated_at)}</p>',
        f'<p class="meta">원본: {html.escape(source_label or "-")} · SQL 방언: {html.escape(dialect or "-")}</p>',
        '<div class="stats">',
    ]
    for label, count in stats:
        parts.append(f'<div class="stat"><strong>{count}</strong><span>{html.escape(label)}</span></div>')
    parts.extend(
        [
            "</div>",
            "</header>",
            "<main>",
            '<div class="controls">',
            '<label for="search">테이블 검색</label>',
            '<input id="search" type="search" placeholder="테이블·컬럼·설명" autocomplete="off" spellcheck="false">',
            f'<p class="count" id="result-count" aria-live="polite">{len(tables)} tables</p>',
            "</div>",
            '<nav class="toc" aria-label="테이블 목차"><ul>',
        ]
    )
    for index, table in enumerate(tables.values(), start=1):
        parts.append(
            f'<li><a href="#table-{index}">{html.escape(table_label(table))}</a></li>'
        )
    parts.extend(["</ul></nav>", '<section class="overview"><h2>테이블 목록</h2><div class="table-wrap"><table>'])
    parts.append(
        "<thead><tr><th>No</th><th>스키마</th><th>테이블</th><th>설명</th><th>컬럼</th><th>PK</th><th>FK</th><th>인덱스</th></tr></thead><tbody>"
    )
    for index, table in enumerate(tables.values(), start=1):
        parts.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{value(table['schema'] or '-')}</td>"
            f'<td><a href="#table-{index}">{value(table["name"])}</a></td>'
            f"<td>{value(table['description'] or '-')}</td>"
            f"<td>{len(table['columns'])}</td>"
            f"<td>{value(', '.join(table['primary_key']) or '-')}</td>"
            f"<td>{len(table['foreign_keys'])}</td>"
            f"<td>{len(table['indexes'])}</td>"
            "</tr>"
        )
    parts.append("</tbody></table></div></section>")

    for index, table in enumerate(tables.values(), start=1):
        search_text = " ".join(
            [
                table_label(table),
                table["description"],
                " ".join(column["name"] for column in table["columns"]),
                " ".join(column["comment"] for column in table["columns"]),
            ]
        ).lower()
        parts.extend(
            [
                f'<section class="table-card" id="table-{index}" data-search="{html.escape(search_text, quote=True)}">',
                f"<h2>{html.escape(table['name'])}"
                + (f' <span class="desc">{html.escape(table["description"])}</span>' if table["description"] else "")
                + "</h2>",
                f'<p class="meta">스키마: {html.escape(table["schema"] or "-")}'
                + (f" · 원본: {html.escape(', '.join(table['source_files']))}" if table["source_files"] else "")
                + "</p>",
                '<div class="table-wrap"><table>',
                "<thead><tr><th>No</th><th>컬럼</th><th>타입</th><th>길이</th><th>PK</th><th>FK</th><th>UNIQUE</th><th>NOT NULL</th><th>DEFAULT</th><th>설명</th><th>비고</th></tr></thead><tbody>",
            ]
        )
        for column_index, column in enumerate(table["columns"], start=1):
            parts.append(
                "<tr>"
                f"<td>{column_index}</td>"
                f"<td>{value(column['name'])}</td>"
                f"<td>{value(column['data_type'])}</td>"
                f"<td>{value(column['length'] or '-')}</td>"
                f"<td>{flag(column['primary_key'])}</td>"
                f"<td>{flag(column['references'])}</td>"
                f"<td>{flag(column['unique'])}</td>"
                f"<td>{flag(not column['nullable'])}</td>"
                f"<td>{value(column['default'] or '-')}</td>"
                f"<td>{value(column['comment'] or '-')}</td>"
                f"<td>{value(column['note'] or '-')}</td>"
                "</tr>"
            )
        parts.append("</tbody></table></div>")

        if table["foreign_keys"]:
            parts.extend(
                [
                    '<div class="subsection"><h3>관계</h3><div class="table-wrap"><table>',
                    "<thead><tr><th>FK</th><th>컬럼</th><th>참조 테이블</th><th>참조 컬럼</th><th>ON DELETE</th><th>ON UPDATE</th></tr></thead><tbody>",
                ]
            )
            for foreign_key in table["foreign_keys"]:
                ref_table = (
                    f"{foreign_key['ref_schema']}.{foreign_key['ref_table']}"
                    if foreign_key["ref_schema"]
                    else foreign_key["ref_table"]
                )
                parts.append(
                    "<tr>"
                    f"<td>{value(foreign_key['name'])}</td>"
                    f"<td>{value(', '.join(foreign_key['columns']) or '-')}</td>"
                    f"<td>{value(ref_table or '-')}</td>"
                    f"<td>{value(', '.join(foreign_key['ref_columns']) or '-')}</td>"
                    f"<td>{value(foreign_key['on_delete'] or '-')}</td>"
                    f"<td>{value(foreign_key['on_update'] or '-')}</td>"
                    "</tr>"
                )
            parts.append("</tbody></table></div></div>")

        if table["indexes"]:
            parts.extend(
                [
                    '<div class="subsection"><h3>인덱스</h3><div class="table-wrap"><table>',
                    "<thead><tr><th>인덱스</th><th>UNIQUE</th><th>컬럼</th></tr></thead><tbody>",
                ]
            )
            for index_entry in table["indexes"]:
                parts.append(
                    "<tr>"
                    f"<td>{value(index_entry['name'])}</td>"
                    f"<td>{flag(index_entry['unique'])}</td>"
                    f"<td>{value(', '.join(index_entry['columns']) or '-')}</td>"
                    "</tr>"
                )
            parts.append("</tbody></table></div></div>")
        parts.append("</section>")

    if data["warnings"]:
        parts.extend(['<section class="warnings"><h2>파싱 메모</h2><ul>'])
        for warning in data["warnings"]:
            parts.append(f"<li>{html.escape(warning)}</li>")
        parts.append("</ul></section>")
    parts.extend(
        [
            "</main>",
            f"<footer>원본: {html.escape(source_label or '-')} · 생성: {html.escape(generated_at)}</footer>",
            f"<script>{javascript}</script>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(parts) + "\n"


def write_xlsx(path, data, tables):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        sys.exit(
            "xlsx를 만들려면 openpyxl이 필요합니다. 스킬의 도구 설치 원칙에 따라 설치한 뒤 다시 시도하세요."
        )

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(size=14, bold=True)
    section_font = Font(bold=True)
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style_header(ws, widths):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        for index, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(index)].width = width
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def write_rows(ws, rows, widths):
        ws.append(rows[0])
        style_header(ws, widths)
        for row in rows[1:]:
            ws.append(row)
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(widths)):
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

    workbook = Workbook()
    summary = workbook.active
    summary.title = "요약"
    summary["A1"] = "테이블 명세서"
    summary["A1"].font = title_font
    summary.merge_cells("A1:D1")
    summary_rows = [
        ("프로젝트", data["project"] or "-"),
        ("생성 시각", data["generated_at"]),
        ("SQL 방언", ", ".join(data["dialects"]) or "-"),
        ("원본", data.get("source_label", "-")),
        ("테이블", len(tables)),
        ("컬럼", data["column_count"]),
        ("관계(FK)", data["fk_count"]),
        ("인덱스", data["index_count"]),
        ("파싱 경고", len(data["warnings"])),
    ]
    for index, (label, value) in enumerate(summary_rows, start=3):
        summary.cell(row=index, column=1, value=label).font = section_font
        summary.cell(row=index, column=2, value=value)
    note_row = len(summary_rows) + 5
    summary.cell(row=note_row, column=1, value="읽는 법").font = section_font
    summary.cell(row=note_row + 1, column=1, value="PK=기본키, FK=외래키, UNIQUE=단일 컬럼 유니크, NOT NULL=필수")
    summary.cell(row=note_row + 2, column=1, value="관계·인덱스는 각 시트에서 확인합니다.")
    summary.column_dimensions["A"].width = 24
    summary.column_dimensions["B"].width = 60

    table_rows = [["No", "스키마", "테이블", "설명", "컬럼", "PK", "FK", "인덱스"]]
    for index, table in enumerate(tables.values(), start=1):
        table_rows.append(
            [
                index,
                table["schema"],
                table["name"],
                table["description"],
                len(table["columns"]),
                ", ".join(table["primary_key"]),
                len(table["foreign_keys"]),
                len(table["indexes"]),
            ]
        )
    write_rows(workbook.create_sheet("테이블 목록"), table_rows, [6, 14, 30, 46, 8, 20, 8, 8])

    column_rows = [
        [
            "No",
            "스키마",
            "테이블",
            "테이블 설명",
            "순서",
            "컬럼",
            "데이터 타입",
            "길이/정밀도",
            "PK",
            "FK",
            "UNIQUE",
            "NOT NULL",
            "DEFAULT",
            "설명",
            "비고",
        ]
    ]
    number = 0
    for table in tables.values():
        for index, column in enumerate(table["columns"], start=1):
            number += 1
            column_rows.append(
                [
                    number,
                    table["schema"],
                    table["name"],
                    table["description"],
                    index,
                    column["name"],
                    column["data_type"],
                    column["length"],
                    "Y" if column["primary_key"] else "",
                    "Y" if column["references"] else "",
                    "Y" if column["unique"] else "",
                    "Y" if not column["nullable"] else "",
                    column["default"],
                    column["comment"],
                    column["note"],
                ]
            )
    write_rows(
        workbook.create_sheet("컬럼 명세"),
        column_rows,
        [6, 14, 30, 46, 7, 24, 22, 14, 6, 6, 9, 10, 24, 46, 24],
    )

    relation_rows = [["FK", "자식 테이블", "자식 컬럼", "부모 테이블", "부모 컬럼", "ON DELETE", "ON UPDATE"]]
    for table in tables.values():
        for foreign_key in table["foreign_keys"]:
            ref_table = (
                f"{foreign_key['ref_schema']}.{foreign_key['ref_table']}"
                if foreign_key["ref_schema"]
                else foreign_key["ref_table"]
            )
            relation_rows.append(
                [
                    foreign_key["name"],
                    table_label(table),
                    ", ".join(foreign_key["columns"]),
                    ref_table,
                    ", ".join(foreign_key["ref_columns"]),
                    foreign_key["on_delete"],
                    foreign_key["on_update"],
                ]
            )
    write_rows(workbook.create_sheet("관계"), relation_rows, [28, 34, 28, 34, 28, 18, 18])

    index_rows = [["테이블", "인덱스", "UNIQUE", "컬럼"]]
    for table in tables.values():
        for index in table["indexes"]:
            index_rows.append(
                [
                    table_label(table),
                    index["name"],
                    "Y" if index["unique"] else "",
                    ", ".join(index["columns"]),
                ]
            )
    write_rows(workbook.create_sheet("인덱스"), index_rows, [34, 34, 9, 60])

    warning_rows = [["파일", "메시지"]]
    for warning in data["warnings"]:
        path = warning.split(": ", 1)[0] if ": " in warning else ""
        warning_rows.append([path, warning])
    if len(warning_rows) == 1:
        warning_rows.append(["-", "없음"])
    write_rows(workbook.create_sheet("파싱 메모"), warning_rows, [60, 100])

    workbook.save(path)


def main():
    args = parse_args()
    if args.db_url:
        tables, warnings, dialects, source_label = introspect_db(
            args.db_url, args.schema, [], include_system=args.include_system
        )
        files = []
        source = "database"
    else:
        files = collect_files(args.ddl)
        tables, warnings, dialects = parse_ddl(files, args.dialect)
        source_label = f"DDL 파일 {len(files)}개"
        source = "ddl"
    if not tables:
        sys.exit("테이블을 찾지 못했습니다. DDL·DB URL과 --dialect·--schema를 확인하세요.")
    tables = finalize_tables(tables)
    data = {
        "project": args.project or Path.cwd().name,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dialects": sorted(set(dialects)),
        "files": [str(path) for path in files],
        "source": source,
        "source_label": source_label,
        "warnings": warnings,
        "column_count": sum(len(table["columns"]) for table in tables.values()),
        "fk_count": sum(len(table["foreign_keys"]) for table in tables.values()),
        "index_count": sum(len(table["indexes"]) for table in tables.values()),
    }
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = outdir / f"{args.name}.md"
    html_path = outdir / f"{args.name}.html"
    xlsx_path = outdir / f"{args.name}.xlsx"
    if "md" in args.formats:
        md_path.write_text(build_markdown(data, tables), encoding="utf-8")
    if "html" in args.formats:
        html_path.write_text(build_html(data, tables), encoding="utf-8")
    if "xlsx" in args.formats:
        write_xlsx(xlsx_path, data, tables)
    summary = {
        "md": str(md_path) if "md" in args.formats else "",
        "html": str(html_path) if "html" in args.formats else "",
        "xlsx": str(xlsx_path) if "xlsx" in args.formats else "",
        "tables": len(tables),
        "columns": data["column_count"],
        "foreign_keys": data["fk_count"],
        "indexes": data["index_count"],
        "warnings": len(warnings),
        "dialects": data["dialects"],
    }
    print(json.dumps(summary, ensure_ascii=False))
    if args.strict and warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
