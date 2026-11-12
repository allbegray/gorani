"""테이블·컬럼·제약 구조와 이름 정규화 유틸.

이 모듈은 표준 라이브러리만 사용한다. 파싱은 parse.py, 출력은 render_sql.py가 맡는다.
"""

import re

RESERVED_WORDS = {
    "all",
    "and",
    "any",
    "array",
    "as",
    "asc",
    "between",
    "by",
    "case",
    "cast",
    "check",
    "collate",
    "column",
    "constraint",
    "create",
    "cross",
    "current_date",
    "current_time",
    "current_timestamp",
    "default",
    "desc",
    "distinct",
    "do",
    "else",
    "end",
    "except",
    "exists",
    "false",
    "for",
    "foreign",
    "from",
    "full",
    "grant",
    "group",
    "having",
    "in",
    "index",
    "inner",
    "insert",
    "intersect",
    "into",
    "is",
    "join",
    "key",
    "left",
    "like",
    "limit",
    "natural",
    "not",
    "null",
    "offset",
    "on",
    "or",
    "order",
    "outer",
    "primary",
    "references",
    "returning",
    "right",
    "select",
    "session_user",
    "table",
    "then",
    "to",
    "true",
    "union",
    "unique",
    "update",
    "user",
    "using",
    "values",
    "when",
    "where",
    "with",
}

PG_TYPE_ALIASES = (
    (r"\bcharacter varying\b", "varchar"),
    (r"\bcharacter\b", "char"),
    (r"\btimestamp\s*(\(\s*\d+\s*\))?\s+with time zone\b", r"timestamptz\1"),
    (r"\btimestamp\s*(\(\s*\d+\s*\))?\s+without time zone\b", r"timestamp\1"),
    (r"\btime\s*(\(\s*\d+\s*\))?\s+with time zone\b", r"timetz\1"),
    (r"\btime\s*(\(\s*\d+\s*\))?\s+without time zone\b", r"time\1"),
    (r"\bbit varying\b", "varbit"),
)

NO_SPACE_BEFORE_PAREN = {
    "in",
    "values",
    "key",
    "unique",
    "references",
    "check",
    "table",
    "any",
    "all",
    "array",
    "primary",
    "foreign",
    "constraint",
    "using",
    "where",
    "and",
    "or",
    "not",
    "exists",
    "between",
    "like",
    "ilike",
    "is",
    "as",
    "on",
    "from",
    "join",
    "over",
}

FUNCTION_NAMES = {
    "now",
    "current_timestamp",
    "current_date",
    "current_time",
    "nextval",
    "currval",
    "setval",
    "coalesce",
    "lower",
    "upper",
    "length",
    "trim",
    "btrim",
    "substring",
    "uuid_generate_v4",
    "gen_random_uuid",
    "jsonb_build_object",
    "json_build_object",
    "date_trunc",
    "extract",
    "to_char",
    "to_date",
    "to_timestamp",
    "greatest",
    "least",
    "abs",
    "round",
    "ceil",
    "floor",
    "concat",
    "replace",
    "md5",
    "random",
    "timezone",
    "count",
    "max",
    "min",
    "sum",
    "avg",
    "array_agg",
    "string_agg",
    "unnest",
}

SERIAL_TYPES = {"bigint": "bigserial", "integer": "serial", "smallint": "smallserial"}
INTEGER_TYPES = {"bigint", "integer", "smallint", "int", "int2", "int4", "int8"}

SAFE_CAST_TARGETS = {
    "text",
    "varchar",
    "character varying",
    "bpchar",
    "character",
    "char",
    "numeric",
    "decimal",
    "integer",
    "int",
    "bigint",
    "smallint",
    "boolean",
    "double precision",
    "real",
    "json",
    "jsonb",
}


def simple_name(name):
    """식별자를 따옴표 없이 비교하기 좋은 형태로 만든다."""
    return (name or "").strip().strip('"`[]').lower()


def quote_identifier(name, dialect="postgres"):
    text = name or ""
    if dialect == "mysql":
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", text) and text.lower() not in RESERVED_WORDS:
            return text
        return "`" + text.replace("`", "``") + "`"
    if re.match(r"^[a-z_][a-z0-9_]*$", text) and text.lower() not in RESERVED_WORDS:
        return text
    return '"' + text.replace('"', '""') + '"'


def qualified_name(schema, name, dialect="postgres", strip_schema=""):
    if schema and schema != strip_schema:
        return f"{quote_identifier(schema, dialect)}.{quote_identifier(name, dialect)}"
    return quote_identifier(name, dialect)


def table_key(schema, name):
    return f"{simple_name(schema)}.{simple_name(name)}" if schema else simple_name(name)


def normalize_type(type_sql, dialect="postgres"):
    text = " ".join((type_sql or "").split())
    if dialect == "postgres":
        for pattern, replacement in PG_TYPE_ALIASES:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\(\s*", "(", text)
    text = re.sub(r"\s*\)", ")", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    return text.strip()


def base_type(type_sql):
    text = simple_name(type_sql)
    match = re.match(r"^([a-z_ ]+?)\s*(?:\(|$)", text)
    return (match.group(1) if match else text).strip()


def strip_casts(expression):
    """문자열 리터럴에 붙은 안전한 캐스트를 제거한다.

    `'active'::public.user_status` -> `'active'`
    `(0)::numeric` -> `0`
    """
    text = expression or ""

    def remove(match):
        literal, target = match.group(1), match.group(2)
        base = simple_name(target.split("(")[0]).replace('"', "")
        if base in SAFE_CAST_TARGETS or re.match(r"^[a-z_][a-z0-9_.]*$", base):
            return literal
        return match.group(0)

    pattern = re.compile(
        r"('(?:[^']|'')*')\s*::\s*((?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_$]*)"
        r"(?:\.(?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_$]*))?(?:\s*\([^)]*\))?(?:\[\])?)"
    )
    text = pattern.sub(remove, text)
    text = re.sub(r"\(\s*(-?\d+(?:\.\d+)?)\s*\)", r"\1", text)
    text = re.sub(r"\bARRAY\s*\[", "[", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\s*\]\s*::\s*[A-Za-z_][A-Za-z0-9_.\[\] ]*", "", text)
    return text


def simplify_any_array(expression):
    """`col = ANY (ARRAY['a','b'])` / `col = ANY (['a'])`를 `col IN ('a','b')`로 바꾼다."""
    text = " ".join((expression or "").split())
    pattern = re.compile(
        r"\(?\s*(?P<left>[A-Za-z_][\w.\"]*)\s*\)?\s*=\s*ANY\s*\(\s*"
        r"(?:ARRAY\s*)?\[(?P<items>[^\]]*)\]\s*(?:::[\w\[\]. ]+)?\s*\)",
        re.IGNORECASE,
    )

    def replace(match):
        items = [item.strip() for item in match.group("items").split(",") if item.strip()]
        return f"{match.group('left')} IN ({', '.join(items)})"

    return pattern.sub(replace, text)


def collapse_parens(expression):
    """`(a >= b)` 같은 불필요한 겉 괄호를 한 겹 벗긴다."""
    text = (expression or "").strip()
    changed = True
    while changed and text.startswith("(") and text.endswith(")"):
        depth = 0
        inner = text[1:-1]
        balanced = True
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(text) - 1:
                    balanced = False
                    break
        if not balanced:
            break
        text = inner.strip()
        changed = True
    return text


def normalize_expression(expression, dialect="postgres"):
    text = collapse_parens(expression)
    if dialect == "postgres":
        text = strip_casts(text)
        text = simplify_any_array(text)
        text = re.sub(r"::[A-Za-z_][\w.\[\] ]*", "", text)
        text = re.sub(r"\bARRAY\s*\[", "(", text, flags=re.IGNORECASE)
    elif dialect == "mysql":
        text = re.sub(r"`([A-Za-z_][A-Za-z0-9_]*)`", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = fix_function_spacing(text)
    return text


def fix_function_spacing(text):
    """`now ()`, `count (*)` 같은 함수 호출의 불필요한 공백을 없앤다.

    단, `IN (`, `VALUES (` 처럼 키워드 뒤 괄호는 한 칸 띄운다.
    """
    pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+\(")

    def replace(match):
        word = match.group(1)
        lowered = word.lower()
        if lowered in NO_SPACE_BEFORE_PAREN and lowered not in FUNCTION_NAMES:
            return f"{word} ("
        return f"{word}("

    return pattern.sub(replace, text)


def new_column(name):
    return {
        "name": name,
        "type": "",
        "nullable": True,
        "default": "",
        "comment": "",
        "auto_increment": False,
        "identity": "",
        "identity_sequence": "",
        "generated": "",
        "collate": "",
        "charset": "",
        "on_update": "",
        "unsigned": False,
        "zerofill": False,
        "check": "",
        "primary_key": False,
        "unique": False,
        "unique_name": "",
        "references": None,
        "raw_extra": [],
    }


def new_table(schema, name, dialect):
    return {
        "schema": schema,
        "name": name,
        "dialect": dialect,
        "comment": "",
        "columns": [],
        "primary_key": None,
        "uniques": [],
        "checks": [],
        "foreign_keys": [],
        "indexes": [],
        "options": [],
        "source_line": 0,
    }


def find_column(table, name):
    target = simple_name(name)
    for column in table["columns"]:
        if simple_name(column["name"]) == target:
            return column
    return None


def add_primary_key(table, name, columns):
    if not columns:
        return
    if table["primary_key"]:
        existing = table["primary_key"]
        if [simple_name(item) for item in existing["columns"]] == [simple_name(item) for item in columns]:
            if not existing["name"]:
                existing["name"] = name or ""
            return
        return
    table["primary_key"] = {"name": name or "", "columns": list(columns)}
    for column in columns:
        target = find_column(table, column)
        if target is not None:
            target["primary_key"] = True
            target["nullable"] = False


def add_unique(table, name, columns):
    if not columns:
        return
    signature = (simple_name(name or ""), tuple(simple_name(item) for item in columns))
    for item in table["uniques"]:
        if (simple_name(item["name"] or ""), tuple(simple_name(col) for col in item["columns"])) == signature:
            return
    table["uniques"].append({"name": name or "", "columns": list(columns)})
    if len(columns) == 1:
        column = find_column(table, columns[0])
        if column is not None:
            column["unique"] = True
            column["unique_name"] = name or ""


def add_check(table, name, expression):
    expression = normalize_expression(expression, table["dialect"])
    if not expression:
        return
    table["checks"].append({"name": name or "", "expression": expression})


def add_foreign_key(table, name, columns, ref_schema, ref_table, ref_columns, on_delete="", on_update="", deferrable=""):
    if not columns or not ref_table:
        return
    key = (
        tuple(simple_name(item) for item in columns),
        simple_name(ref_table),
        tuple(simple_name(item) for item in ref_columns),
    )
    for item in table["foreign_keys"]:
        if (
            tuple(simple_name(col) for col in item["columns"]),
            simple_name(item["ref_table"]),
            tuple(simple_name(col) for col in item["ref_columns"]),
        ) == key:
            return
    table["foreign_keys"].append(
        {
            "name": name or "",
            "columns": list(columns),
            "ref_schema": ref_schema or "",
            "ref_table": ref_table,
            "ref_columns": list(ref_columns),
            "on_delete": on_delete or "",
            "on_update": on_update or "",
            "deferrable": deferrable or "",
        }
    )


def add_index(table, name, columns, unique=False, method="", where="", index_type=""):
    if not columns:
        return
    signature = (simple_name(name or ""), tuple(simple_name(item) for item in columns), bool(unique))
    for item in table["indexes"]:
        if (simple_name(item["name"] or ""), tuple(simple_name(col) for col in item["columns"]), item["unique"]) == signature:
            return
    table["indexes"].append(
        {
            "name": name or "",
            "columns": list(columns),
            "unique": bool(unique),
            "method": method or "",
            "where": where or "",
            "type": index_type or "",
        }
    )


def column_signature(column):
    return (
        simple_name(column["name"]),
        normalize_type(column["type"]),
        bool(column["nullable"]),
    )
