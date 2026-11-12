"""테이블 구조를 사람이 작성한 스타일의 DDL로 렌더링한다.

렌더링 규칙:
- PK·UNIQUE가 단일 컬럼이면 컬럼 줄에 인라인으로 붙인다.
- FK도 단일 컬럼이면 컬럼 줄에 REFERENCES로 붙인다.
- 여러 컬럼이 걸린 PK·UNIQUE·FK·CHECK는 CREATE TABLE 안의 CONSTRAINT 줄로 둔다.
- INDEX는 MySQL이면 테이블 안 KEY로, PostgreSQL이면 테이블 바로 뒤 CREATE INDEX로 둔다.
- FK 참조 대상이 먼저 오도록 테이블 순서를 재배열한다.
- pg_dump가 만든 이름(users_pkey, users_email_key)은 pk_users, uq_users_email로 바꾼다.
- 컬럼명·타입 시작 위치를 세로로 맞춘다.
"""

import re

from .model import (
    INTEGER_TYPES,
    SERIAL_TYPES,
    base_type,
    quote_identifier,
    qualified_name,
    simple_name,
    table_key,
)


class Options:
    def __init__(self, **kwargs):
        self.dialect = kwargs.get("dialect", "postgres")
        self.strip_schema = kwargs.get("strip_schema", "")
        self.comments = kwargs.get("comments", "inline")
        self.rename_constraints = kwargs.get("rename_constraints", True)
        self.serial = kwargs.get("serial", True)
        self.header = kwargs.get("header", True)
        self.title = kwargs.get("title", "")
        self.database = kwargs.get("database", "")
        self.align = kwargs.get("align", True)
        self.enums = kwargs.get("enums", True)


def render(result, options):
    tables = order_tables(result.tables.values())
    blocks = []

    if options.dialect == "postgres" and options.enums:
        for enum in result.types:
            values = enum.get("values") or []
            if not values:
                continue
            name = qualified_name(enum.get("schema", ""), enum["name"], options.dialect, options.strip_schema)
            rendered = ", ".join(sql_string(value) for value in values)
            blocks.append(f"CREATE TYPE {name} AS ENUM ({rendered});")

    for table in tables:
        blocks.append(render_table(table, options))

    parts = []
    if options.header:
        parts.append(build_header(result, options))
    parts.extend(blocks)
    text = "\n\n".join(part for part in parts if part)
    return text.rstrip() + "\n"


def build_header(result, options):
    lines = [f"-- {options.title}" if options.title else "-- 스키마 정의"]
    meta = []
    if options.database:
        meta.append(f"database: {options.database}")
    meta.append(f"tables: {len(result.tables)}")
    lines.append("-- " + " / ".join(meta))
    return "\n".join(lines)


def order_tables(tables):
    """FK 참조 대상이 먼저 오도록 정렬한다. 순환 참조는 이름 순으로 남긴다."""
    by_name = {simple_name(table["name"]): table for table in tables}
    ordered = []
    visiting = set()
    visited = set()

    def dependencies(table):
        found = []
        for foreign_key in table["foreign_keys"]:
            target = by_name.get(simple_name(foreign_key["ref_table"]))
            if target is not None and target is not table:
                found.append(target)
        return found

    def visit(table):
        key = table_key(table["schema"], table["name"])
        if key in visited or key in visiting:
            return
        visiting.add(key)
        for dependency in sorted(dependencies(table), key=lambda item: table_key(item["schema"], item["name"])):
            visit(dependency)
        visiting.discard(key)
        visited.add(key)
        ordered.append(table)

    for table in sorted(tables, key=lambda item: table_key(item["schema"], item["name"])):
        visit(table)
    return ordered


def render_table(table, options):
    name = qualified_name(table["schema"], table["name"], options.dialect, options.strip_schema)
    lines = []

    if table["comment"] and options.comments == "text":
        lines.append(f"-- {table['comment']}")

    for column in table["columns"]:
        column["inline"] = {}

    attachments = collect_inline_attachments(table, options)

    body = []
    for column in table["columns"]:
        if column["comment"] and options.comments == "text":
            body.append(f"    -- {column['comment']}")
        body.append(render_column(column, attachments.get(column["name"], {}), table, options))

    for line in render_wide_constraints(table, options):
        body.append(line)

    if options.align:
        body = align_body(body)

    lines.append(f"CREATE TABLE {name} (")
    lines.extend(with_commas(body))
    lines.append(")" + table_options(table, options) + ";")

    comment_block = table_comments(table, options)
    if comment_block:
        lines.append("")
        lines.append(comment_block)

    if options.dialect != "mysql":
        index_statements = []
        for index in table["indexes"]:
            statement = render_index(table, index, options)
            if statement:
                index_statements.append(statement)
        if index_statements:
            lines.append("")
            lines.extend(index_statements)

    return "\n".join(lines)


def collect_inline_attachments(table, options):
    """단일 컬럼 PK·UNIQUE·FK·CHECK를 어느 컬럼 줄에 붙일지 정한다."""
    attachments = {}

    def bucket(name):
        return attachments.setdefault(name, {"primary_key": False, "unique": False, "references": [], "checks": []})

    primary_key = table["primary_key"]
    if primary_key and len(primary_key["columns"]) == 1:
        column = find_column(table, primary_key["columns"][0])
        if column is not None:
            bucket(column["name"])["primary_key"] = True
            column["nullable"] = False
            table["primary_key"] = None
    elif primary_key and len(primary_key["columns"]) > 1:
        pass

    for unique in table["uniques"]:
        if len(unique["columns"]) == 1:
            column = find_column(table, unique["columns"][0])
            if column is not None and not bucket(column["name"])["primary_key"]:
                bucket(column["name"])["unique"] = True
                unique["rendered"] = True

    for foreign_key in table["foreign_keys"]:
        if len(foreign_key["columns"]) == 1 and options.dialect != "mysql":
            column = find_column(table, foreign_key["columns"][0])
            if column is not None:
                bucket(column["name"])["references"].append(foreign_key)
                foreign_key["rendered"] = True

    for check in table["checks"]:
        columns = referenced_columns(table, check["expression"])
        if len(columns) == 1:
            bucket(columns[0])["checks"].append(check)
            check["rendered"] = True

    return attachments


def referenced_columns(table, expression):
    names = []
    for column in table["columns"]:
        if re.search(rf"(?<![\w.]){re.escape(column['name'])}(?![\w])", expression or "", re.IGNORECASE):
            names.append(column["name"])
    return names


def render_column(column, attached, table, options):
    parts = [quote_identifier(column["name"], options.dialect), render_type(column, table, options)]

    if column["collate"] and options.dialect == "mysql":
        parts.append(f"COLLATE {column['collate']}")

    is_serial = parts[1] in SERIAL_TYPES.values()

    if column["generated"]:
        parts.append(f"GENERATED ALWAYS AS ({column['generated']}) STORED")
    elif not is_serial:
        if column["identity"] == "AUTO_INCREMENT":
            parts.append("AUTO_INCREMENT" if options.dialect == "mysql" else "GENERATED BY DEFAULT AS IDENTITY")
        elif column["identity"]:
            parts.append(f"GENERATED {column['identity']} AS IDENTITY")
        elif column["auto_increment"]:
            parts.append("AUTO_INCREMENT" if options.dialect == "mysql" else "GENERATED BY DEFAULT AS IDENTITY")

    if column["default"] and not is_serial:
        parts.append(f"DEFAULT {column['default']}")

    if column["on_update"]:
        parts.append(f"ON UPDATE {column['on_update']}")

    if not column["nullable"] and not attached.get("primary_key") and not is_serial:
        parts.append("NOT NULL")

    if attached.get("primary_key"):
        parts.append("PRIMARY KEY")
    if attached.get("unique"):
        parts.append("UNIQUE")

    for foreign_key in attached.get("references", []):
        parts.append(render_reference(foreign_key, options))

    for check in attached.get("checks", []):
        parts.append(f"CHECK ({check['expression']})")

    if column["comment"] and options.comments == "inline" and options.dialect == "mysql":
        parts.append(f"COMMENT {sql_string(column['comment'])}")

    return "    " + " ".join(parts)


def render_reference(foreign_key, options):
    target = qualified_name(
        foreign_key["ref_schema"], foreign_key["ref_table"], options.dialect, options.strip_schema
    )
    columns = ", ".join(quote_identifier(item, options.dialect) for item in foreign_key["ref_columns"])
    text = f"REFERENCES {target} ({columns})"
    if foreign_key["on_delete"]:
        text += f" ON DELETE {foreign_key['on_delete']}"
    if foreign_key["on_update"]:
        text += f" ON UPDATE {foreign_key['on_update']}"
    if foreign_key["deferrable"]:
        text += f" {foreign_key['deferrable']}"
    return text


def render_type(column, table, options):
    text = column["type"]
    if options.dialect == "mysql":
        if column["unsigned"]:
            text += " unsigned"
        if column["zerofill"]:
            text += " zerofill"
        return text
    if options.strip_schema:
        text = re.sub(
            rf'^{re.escape(options.strip_schema)}\.(\w+)',
            r"\1",
            text,
            flags=re.IGNORECASE,
        )
    base = base_type(text)
    if options.serial and base in INTEGER_TYPES and is_serial_candidate(column):
        return SERIAL_TYPES.get(base, text)
    return text


def is_serial_candidate(column):
    if (column["default"] or "").lower().find("nextval(") >= 0:
        return True
    return column["identity"] == "AUTO_INCREMENT" or column["auto_increment"]


def render_wide_constraints(table, options):
    lines = []

    primary_key = table["primary_key"]
    if primary_key and len(primary_key["columns"]) > 1:
        name = constraint_name(table, primary_key["name"], "pk", primary_key["columns"], options)
        columns = ", ".join(quote_identifier(item, options.dialect) for item in primary_key["columns"])
        lines.append(f"    CONSTRAINT {name} PRIMARY KEY ({columns})")

    for unique in table["uniques"]:
        if unique.get("rendered"):
            continue
        name = constraint_name(table, unique["name"], "uq", unique["columns"], options)
        columns = ", ".join(quote_identifier(item, options.dialect) for item in unique["columns"])
        lines.append(f"    CONSTRAINT {name} UNIQUE ({columns})")

    for check in table["checks"]:
        if check.get("rendered"):
            continue
        name = constraint_name(table, check["name"], "ck", [], options, expression=check["expression"])
        lines.append(f"    CONSTRAINT {name} CHECK ({check['expression']})")

    for foreign_key in table["foreign_keys"]:
        if foreign_key.get("rendered"):
            continue
        name = constraint_name(table, foreign_key["name"], "fk", foreign_key["columns"], options)
        columns = ", ".join(quote_identifier(item, options.dialect) for item in foreign_key["columns"])
        target = qualified_name(
            foreign_key["ref_schema"], foreign_key["ref_table"], options.dialect, options.strip_schema
        )
        ref_columns = ", ".join(
            quote_identifier(item, options.dialect) for item in foreign_key["ref_columns"]
        )
        parts = [f"    CONSTRAINT {name} FOREIGN KEY ({columns}) REFERENCES {target} ({ref_columns})"]
        if foreign_key["on_delete"]:
            parts.append(f"ON DELETE {foreign_key['on_delete']}")
        if foreign_key["on_update"]:
            parts.append(f"ON UPDATE {foreign_key['on_update']}")
        if foreign_key["deferrable"]:
            parts.append(foreign_key["deferrable"])
        lines.append(" ".join(parts))

    if options.dialect == "mysql":
        for index in table["indexes"]:
            if index.get("rendered") or already_unique(table, index["columns"]):
                continue
            name = index_name(table, index, options, prefix="uq" if index["unique"] else "idx")
            columns = ", ".join(quote_identifier(item, options.dialect) for item in index["columns"])
            keyword = "UNIQUE KEY" if index["unique"] else "KEY"
            lines.append(f"    {keyword} {name} ({columns})")

    return lines


def table_options(table, options):
    if options.dialect != "mysql":
        return ""
    values = {}
    for option in table["options"]:
        match = re.match(r"^([A-Za-z_ ]+?)\s*=\s*(.+)$", option)
        if match:
            values[match.group(1).strip().upper()] = match.group(2).strip()

    parts = ["ENGINE=InnoDB"]
    charset = values.get("DEFAULT CHARSET") or values.get("CHARSET") or values.get("CHARACTER SET")
    if charset:
        parts.append(f"DEFAULT CHARSET={charset}")
    if values.get("COLLATE"):
        parts.append(f"COLLATE={values['COLLATE']}")
    return " " + " ".join(parts)


def table_comments(table, options):
    if options.dialect != "postgres" or options.comments != "inline":
        return ""
    name = qualified_name(table["schema"], table["name"], options.dialect, options.strip_schema)
    lines = []
    if table["comment"]:
        lines.append(f"COMMENT ON TABLE {name} IS {sql_string(table['comment'])};")
    for column in table["columns"]:
        if column["comment"]:
            lines.append(
                f"COMMENT ON COLUMN {name}.{quote_identifier(column['name'], options.dialect)} "
                f"IS {sql_string(column['comment'])};"
            )
    return "\n".join(lines)


def render_index(table, index, options):
    if index.get("rendered") or already_unique(table, index["columns"]):
        return ""
    name = index_name(table, index, options, prefix="uq" if index["unique"] else "idx")
    table_name = qualified_name(table["schema"], table["name"], options.dialect, options.strip_schema)
    columns = render_index_columns(index["columns"], options)
    keyword = "CREATE UNIQUE INDEX" if index["unique"] else "CREATE INDEX"
    statement = f"{keyword} {name} ON {table_name} ({columns})"
    if index["where"]:
        statement += f" WHERE {index['where']}"
    return statement + ";"


def sql_string(value):
    return "'" + str(value).replace("'", "''") + "'"


def with_commas(body):
    """마지막 항목만 빼고 쉼표를 붙인다. 주석 줄은 그대로 둔다."""
    meaningful = [index for index, line in enumerate(body) if not line.strip().startswith("--")]
    if not meaningful:
        return list(body)
    last = meaningful[-1]
    output = []
    for index, line in enumerate(body):
        if index == last or line.strip().startswith("--"):
            output.append(line)
        else:
            output.append(line + ",")
    return output


def find_column(table, name):
    target = simple_name(name)
    for column in table["columns"]:
        if simple_name(column["name"]) == target:
            return column
    return None


def already_unique(table, columns):
    signature = [simple_name(item) for item in columns]
    for unique in table["uniques"]:
        if [simple_name(item) for item in unique["columns"]] == signature:
            return True
    if len(columns) == 1:
        column = find_column(table, columns[0])
        if column is not None and column["unique"]:
            return True
    return False


def render_index_columns(columns, options):
    return ", ".join(render_index_column(item, options) for item in columns)


def render_index_column(column, options):
    text = (column or "").strip()
    if re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", text):
        return quote_identifier(text, options.dialect)
    if re.match(r'^"[^"]+"$', text) or re.match(r"^`[^`]+`$", text):
        return quote_identifier(text[1:-1], options.dialect)
    return text


def index_name(table, index, options, prefix="idx"):
    if index["name"] and not (options.rename_constraints and is_dump_name(index["name"], table)):
        return quote_identifier(index["name"], options.dialect)
    return quote_identifier(build_name(prefix, table["name"], index["columns"]), options.dialect)


def constraint_name(table, name, prefix, columns, options, expression=""):
    if name and not (options.rename_constraints and is_dump_name(name, table)):
        return quote_identifier(name, options.dialect)
    if prefix == "ck" and not columns:
        columns = referenced_columns(table, expression)[:2]
    return quote_identifier(build_name(prefix, table["name"], columns), options.dialect)


def is_dump_name(name, table):
    """pg_dump가 자동으로 만든 이름인지 확인한다."""
    lowered = name.lower()
    table_name = table["name"].lower()
    if not lowered.startswith(table_name + "_"):
        return False
    return bool(re.match(r"_(pkey|key|fkey|check|excl)$", lowered[len(table_name) :]))


def build_name(prefix, table_name, columns):
    parts = [prefix, table_name]
    for column in columns[:3]:
        cleaned = re.sub(r"[^0-9A-Za-z_]", "", simple_name(column))
        if cleaned:
            parts.append(cleaned)
    name = "_".join(part for part in parts if part)
    if len(name) > 60:
        name = name[:60].rstrip("_")
    return name


def align_body(lines):
    """컬럼명과 타입 시작 위치를 세로로 맞춘다. 주석·제약 줄은 그대로 둔다."""
    parsed = []
    widths = [0, 0]
    for line in lines:
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("--")
            or stripped.startswith("CONSTRAINT")
            or stripped.startswith("KEY ")
            or stripped.startswith("UNIQUE KEY ")
            or stripped.startswith("INDEX ")
            or stripped.startswith("FULLTEXT ")
            or stripped.startswith("SPATIAL ")
        ):
            parsed.append(None)
            continue
        cells = split_column_line(stripped)
        if cells is None:
            parsed.append(None)
            continue
        parsed.append(cells)
        widths[0] = max(widths[0], len(cells[0]))
        widths[1] = max(widths[1], len(cells[1]))

    output = []
    for line, cells in zip(lines, parsed):
        if cells is None:
            output.append(line.rstrip())
            continue
        name, data_type, rest = cells
        text = name.ljust(widths[0] + 1) + data_type.ljust(widths[1] + 1)
        if rest:
            text += rest
        output.append("    " + text.rstrip())
    return output


def split_column_line(text):
    match = re.match(r'^("(?:[^"]|"")+"|`[^`]+`|\S+)\s+(.*)$', text)
    if not match:
        return None
    name = match.group(1)
    rest = match.group(2)
    type_match = re.match(
        r"^((?:[A-Za-z_][\w ]*?)(?:\([^)]*\))?(?:\s*\[\])?)"
        r"(?=\s+(?:NOT\s+NULL|NULL|DEFAULT|PRIMARY|UNIQUE|REFERENCES|CHECK|COLLATE|"
        r"GENERATED|AUTO_INCREMENT|COMMENT|ON\s+UPDATE)\b|$)",
        rest,
        re.IGNORECASE,
    )
    if not type_match:
        return None
    data_type = type_match.group(1).strip()
    if not data_type:
        return None
    tail = rest[type_match.end() :].strip()
    return [name, data_type, tail]
