"""SQL DDL 입력 어댑터.

sqlglot은 이 모듈에서만 import한다. sqlglot이 없어도 모듈 import는 되고,
실제 파싱을 시작할 때 parse_ddl이 설치 안내와 함께 종료한다.
"""

import re
import sys
from pathlib import Path

from .constants import DIALECTS
from .model import (
    add_foreign_key,
    add_index,
    add_unique,
    mark_columns,
    new_column,
    new_table,
    split_type,
    table_key,
)

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    sqlglot = None
    exp = None


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
