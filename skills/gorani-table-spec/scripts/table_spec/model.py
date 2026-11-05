"""테이블 구조를 만들고 리포트 모델로 묶는다.

이 모듈은 sqlglot·SQLAlchemy·openpyxl을 import하지 않는다. DDL·DB 입력 어댑터가
같은 테이블 구조를 쓰도록 순수 로직만 둔다.
"""

import re

from .constants import SCHEMA_VERSION


def table_key(schema, name):
    return f"{schema}.{name}" if schema else name


def split_type(type_sql):
    text = (type_sql or "-").strip()
    match = re.match(r"^([^(]+?)(?:\((.*)\))?$", text)
    if not match:
        return text, ""
    return match.group(1).strip(), (match.group(2) or "").strip()


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


def build_report_model(
    project,
    generated_at,
    dialects,
    files,
    source,
    source_label,
    tables,
    warnings,
    sources,
):
    """Markdown·HTML·XLSX 렌더러가 함께 쓰는 JSON 직렬화 가능 모델을 만든다."""
    table_list = list(tables.values()) if isinstance(tables, dict) else list(tables)
    table_list.sort(key=lambda table: table_key(table["schema"], table["name"]))
    summary = {
        "tables": len(table_list),
        "columns": sum(len(table["columns"]) for table in table_list),
        "foreign_keys": sum(len(table["foreign_keys"]) for table in table_list),
        "indexes": sum(len(table["indexes"]) for table in table_list),
        "warnings": len(warnings),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "project": project,
            "generated_at": generated_at,
            "source": source,
            "source_label": source_label,
            "dialects": sorted(set(dialects)),
            "files": [str(path) for path in files],
            "generator": "gorani-table-spec",
        },
        "summary": summary,
        "tables": table_list,
        "warnings": list(warnings),
        "sources": list(sources),
    }
