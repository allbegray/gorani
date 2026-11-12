"""dump SQL을 테이블 구조로 해석한다.

sqlglot을 쓰지 않고 문법 요소를 직접 인식한다. dump는 표준 문법에서 조금씩
벗어난 구문(PG의 ALTER TABLE ONLY, MySQL의 /*!40101 */ 조건부 주석)을 쓰기
때문에, 필요한 구문만 정확히 처리하고 모르는 구문은 warnings에 남긴다.
"""

import re

from .model import (
    add_check,
    add_foreign_key,
    add_index,
    add_primary_key,
    add_unique,
    find_column,
    new_column,
    new_table,
    normalize_expression,
    normalize_type,
    simple_name,
)
from .tokenizer import matching_paren, split_statements, split_top_level, unquote

CREATE_TABLE = re.compile(
    r"^CREATE\s+(?:(?:GLOBAL|LOCAL)\s+)?(?:(?:TEMPORARY|TEMP|UNLOGGED)\s+)?TABLE\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>.+?)\s*(?:\(|AS\b|LIKE\b|$)",
    re.IGNORECASE | re.DOTALL,
)
CREATE_INDEX = re.compile(
    r"^CREATE\s+(?P<unique>UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?"
    r"(?P<name>[^\s(]+)\s+ON\s+(?:ONLY\s+)?(?P<table>[^\s(]+)\s*(?P<rest>.*)$",
    re.IGNORECASE | re.DOTALL,
)
ALTER_TABLE = re.compile(
    r"^ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?(?P<table>[^\s]+)\s+(?P<rest>.*)$",
    re.IGNORECASE | re.DOTALL,
)
COMMENT_ON = re.compile(
    r"^COMMENT\s+ON\s+(?P<kind>TABLE|COLUMN)\s+(?P<target>[^\s]+)\s+IS\s+(?P<value>.+)$",
    re.IGNORECASE | re.DOTALL,
)
CREATE_TYPE = re.compile(r"^CREATE\s+TYPE\s+(?P<name>[^\s]+)\s+AS\s+ENUM", re.IGNORECASE | re.DOTALL)
CREATE_SEQUENCE = re.compile(r"^CREATE\s+SEQUENCE\s+(?P<name>[^\s]+)", re.IGNORECASE)
CREATE_SCHEMA = re.compile(r"^CREATE\s+SCHEMA\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[^\s;]+)", re.IGNORECASE)
SET_DEFAULT = re.compile(
    r"^ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<table>[^\s]+)\s+ALTER\s+(?:COLUMN\s+)?(?P<column>[^\s]+)\s+SET\s+DEFAULT\s+(?P<value>.+)$",
    re.IGNORECASE | re.DOTALL,
)
ADD_IDENTITY = re.compile(
    r"^ALTER\s+TABLE\s+(?:ONLY\s+)?(?P<table>[^\s]+)\s+ALTER\s+(?:COLUMN\s+)?(?P<column>[^\s]+)\s+"
    r"ADD\s+GENERATED\s+(?P<kind>ALWAYS|BY\s+DEFAULT)\s+AS\s+IDENTITY\s*(?P<body>\(.*\))?$",
    re.IGNORECASE | re.DOTALL,
)
OWNED_BY = re.compile(
    r"^ALTER\s+SEQUENCE\s+(?P<sequence>[^\s]+)\s+OWNED\s+BY\s+(?P<table>[^\s.]+)\.(?P<column>[^\s;]+)$",
    re.IGNORECASE,
)

PG_NOISE_PREFIXES = (
    "SET ",
    "SELECT PG_CATALOG.SET_CONFIG",
    "SELECT SET_CONFIG",
    "SELECT PG_CATALOG.SETVAL",
    "SELECT SETVAL",
    "\\",
    "ALTER TABLE ONLY",
    "ALTER TABLE ",
    "ALTER SEQUENCE ",
    "ALTER TYPE ",
    "ALTER FUNCTION ",
    "ALTER SCHEMA ",
    "ALTER DATABASE ",
    "ALTER DEFAULT PRIVILEGES ",
    "ALTER VIEW ",
    "ALTER MATERIALIZED VIEW ",
    "ALTER INDEX ",
    "ALTER TRIGGER ",
    "ALTER POLICY ",
    "ALTER ROUTINE ",
    "ALTER FOREIGN",
    "GRANT ",
    "REVOKE ",
    "COMMENT ON EXTENSION",
    "COMMENT ON SCHEMA",
    "COMMENT ON INDEX",
    "COMMENT ON CONSTRAINT",
    "COMMENT ON TRIGGER",
    "COMMENT ON FUNCTION",
    "COMMENT ON VIEW",
    "COMMENT ON SEQUENCE",
    "COMMENT ON TYPE",
    "COMMENT ON EXTENSION",
    "CREATE EXTENSION",
    "CREATE FUNCTION",
    "CREATE PROCEDURE",
    "CREATE TRIGGER",
    "CREATE RULE",
    "CREATE VIEW",
    "CREATE MATERIALIZED VIEW",
    "CREATE OR REPLACE",
    "CREATE PUBLICATION",
    "CREATE SUBSCRIPTION",
    "CREATE POLICY",
    "CREATE ROLE",
    "CREATE USER",
    "CREATE DATABASE",
    "CREATE TABLESPACE",
    "CREATE CAST",
    "CREATE AGGREGATE",
    "CREATE OPERATOR",
    "CREATE TEXT SEARCH",
    "CREATE FOREIGN",
    "CREATE SERVER",
    "CREATE STATISTICS",
    "CREATE COLLATION",
    "CREATE DOMAIN",
    "REFRESH MATERIALIZED VIEW",
    "SECURITY LABEL",
    "LOCK TABLE",
    "COPY ",
    "INSERT INTO",
    "UPDATE ",
    "DELETE FROM",
    "TRUNCATE ",
    "ANALYZE ",
    "VACUUM ",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "START TRANSACTION",
    "SAVEPOINT ",
    "RELEASE SAVEPOINT",
    "DO ",
    "CALL ",
)

MYSQL_NOISE_PATTERNS = (
    re.compile(r"^/\*!\d+\s+SET\b", re.IGNORECASE),
    re.compile(r"^SET\b", re.IGNORECASE),
    re.compile(r"^LOCK\s+TABLES\b", re.IGNORECASE),
    re.compile(r"^UNLOCK\s+TABLES\b", re.IGNORECASE),
    re.compile(r"^DROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"^DROP\s+VIEW\b", re.IGNORECASE),
    re.compile(r"^DROP\s+TRIGGER\b", re.IGNORECASE),
    re.compile(r"^DELIMITER\b", re.IGNORECASE),
    re.compile(r"^USE\b", re.IGNORECASE),
    re.compile(r"^CREATE\s+DATABASE\b", re.IGNORECASE),
    re.compile(r"^CREATE\s+USER\b", re.IGNORECASE),
    re.compile(r"^GRANT\b", re.IGNORECASE),
    re.compile(r"^REVOKE\b", re.IGNORECASE),
    re.compile(r"^FLUSH\b", re.IGNORECASE),
    re.compile(r"^ALTER\s+TABLE\b", re.IGNORECASE),
)

PG_ALTER_ADD_CONSTRAINT = re.compile(
    r"^ADD\s+CONSTRAINT\s+(?P<name>[^\s]+)\s+(?P<body>.+)$", re.IGNORECASE | re.DOTALL
)
PG_ALTER_ADD_NO_NAME = re.compile(
    r"^ADD\s+(?P<body>(?:PRIMARY\s+KEY|UNIQUE|FOREIGN\s+KEY|CHECK|CONSTRAINT)\b.+)$",
    re.IGNORECASE | re.DOTALL,
)
PG_ALTER_ALTER_COLUMN = re.compile(
    r"^ALTER\s+(?:COLUMN\s+)?(?P<column>[^\s]+)\s+(?P<body>.+)$", re.IGNORECASE | re.DOTALL
)
PG_ALTER_ADD_COLUMN = re.compile(
    r"^ADD\s+(?:COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?(?P<body>.+)$", re.IGNORECASE | re.DOTALL
)
PG_ALTER_OWNER = re.compile(r"^OWNER\s+TO\s+.+$", re.IGNORECASE | re.DOTALL)

TABLE_CONSTRAINT_START = re.compile(
    r"^(?:CONSTRAINT\s+(?P<name>[^\s]+)\s+)?"
    r"(?P<kind>PRIMARY\s+KEY|UNIQUE(?:\s+(?:KEY|INDEX))?|FOREIGN\s+KEY|CHECK|KEY|INDEX|FULLTEXT(?:\s+KEY)?|SPATIAL(?:\s+KEY)?)\b"
    r"(?P<body>.*)$",
    re.IGNORECASE | re.DOTALL,
)

INLINE_CONSTRAINT = re.compile(
    r"\b(?P<kind>NOT\s+NULL|NULL|PRIMARY\s+KEY|UNIQUE(?:\s+KEY)?|DEFAULT|REFERENCES|"
    r"CHECK|COLLATE|AUTO_INCREMENT|AUTOINCREMENT|GENERATED|ON\s+UPDATE|COMMENT|"
    r"CHARACTER\s+SET|CHARSET|COLLATE)\b",
    re.IGNORECASE,
)

COLUMN_END_CONSTRAINTS = (
    "NOT NULL",
    "NULL",
    "PRIMARY KEY",
    "UNIQUE",
    "DEFAULT",
    "REFERENCES",
    "CHECK",
    "COLLATE",
    "AUTO_INCREMENT",
    "AUTOINCREMENT",
    "GENERATED",
    "ON UPDATE",
    "COMMENT",
    "CHARACTER SET",
    "CHARSET",
)


class ParseResult:
    def __init__(self):
        self.tables = {}
        self.types = []
        self.sequences = []
        self.schemas = []
        self.warnings = []
        self.skipped = 0
        self.dialect = "postgres"

    def table(self, schema, name, dialect, line):
        from .model import table_key

        key = table_key(schema, name)
        if key not in self.tables:
            table = new_table(schema, name, dialect)
            table["source_line"] = line
            self.tables[key] = table
        return self.tables[key]


def detect_dialect(text):
    lowered = text.lower()
    score = {"postgres": 0, "mysql": 0, "mssql": 0, "oracle": 0, "sqlite": 0}
    if "pg_catalog" in lowered or "postgresql database dump" in lowered:
        score["postgres"] += 5
    if "mysqldump" in lowered or "storage engine" in lowered or "engine=innodb" in lowered:
        score["mysql"] += 5
    if "character varying" in lowered or "::" in text:
        score["postgres"] += 3
    if "`" in text:
        score["mysql"] += 3
    if "auto_increment" in lowered:
        score["mysql"] += 2
    if "nvarchar" in lowered or "identity(" in lowered.replace(" ", ""):
        score["mssql"] += 3
    if "varchar2" in lowered or "number(" in lowered:
        score["oracle"] += 3
    if "auto_increment" not in lowered and "serial" in lowered:
        score["postgres"] += 2
    best = max(score, key=lambda key: score[key])
    return best if score[best] > 0 else "postgres"


def split_object_name(text):
    """`public.users` 또는 `` `shop`.`users` `` -> (schema, name)."""
    text = text.strip().rstrip(";").strip()
    parts = split_qualified(text)
    if len(parts) >= 2:
        return unquote(parts[-2]), unquote(parts[-1])
    return "", unquote(parts[0]) if parts else ""


def split_qualified(text):
    parts = []
    buffer = []
    quote = None
    for char in text:
        if quote:
            buffer.append(char)
            if char == quote:
                quote = None
            continue
        if char in ('"', "`"):
            quote = char
            buffer.append(char)
            continue
        if char == ".":
            parts.append("".join(buffer).strip())
            buffer = []
            continue
        buffer.append(char)
    parts.append("".join(buffer).strip())
    return [part for part in parts if part]


def strip_conditional_comments(sql):
    """MySQL의 /*!40101 ... */ 조건부 주석을 안쪽 SQL로 바꾼다."""
    pattern = re.compile(r"/\*!\d*\s?(.*?)\*/", re.DOTALL)

    def replace(match):
        inner = match.group(1).strip()
        if re.match(r"^(SET|ALTER|CREATE|INSERT|LOCK|UNLOCK|DROP)\b", inner, re.IGNORECASE):
            return inner
        return ""

    return pattern.sub(replace, sql)


def strip_copy_blocks(text):
    """pg_dump의 COPY ... FROM stdin; 데이터 블록을 제거한다.

    데이터는 스키마 정의가 아니고, 남겨 두면 문장 분리가 깨진다.
    """
    lines = text.splitlines()
    output = []
    index = 0
    length = len(lines)
    while index < length:
        line = lines[index]
        if re.match(r"^\s*COPY\s+.+\bFROM\s+stdin\s*;\s*$", line, re.IGNORECASE):
            index += 1
            while index < length and lines[index].strip() != "\\.":
                index += 1
            index += 1
            output.append("-- [데이터 블록 생략]")
            continue
        output.append(line)
        index += 1
    return "\n".join(output)


def parse_dump(text, dialect="auto"):
    result = ParseResult()
    if dialect in ("", "auto", None):
        dialect = detect_dialect(text)
    result.dialect = dialect
    text = strip_copy_blocks(text)
    statements = split_statements(text)
    for statement in statements:
        sql = statement["sql"].strip()
        if not sql:
            continue
        parsing_sql = strip_conditional_comments(sql) if dialect == "mysql" else sql
        parse_statement(parsing_sql.strip(), statement["line"], result)
    finalize(result)
    return result


def parse_statement(sql, line, result):
    upper = sql.upper()

    match = CREATE_TABLE.match(sql)
    if match:
        parse_create_table(sql, match, line, result)
        return

    match = CREATE_INDEX.match(sql)
    if match:
        parse_create_index(sql, match, result)
        return

    match = CREATE_TYPE.match(sql)
    if match:
        result.types.append(
            {"schema": split_object_name(match.group("name"))[0], "name": split_object_name(match.group("name"))[1], "values": parse_enum_values(sql)}
        )
        return

    match = CREATE_SEQUENCE.match(sql)
    if match:
        result.sequences.append(split_object_name(match.group("name"))[1])
        return

    match = CREATE_SCHEMA.match(sql)
    if match:
        result.schemas.append(unquote(match.group("name")))
        return

    match = COMMENT_ON.match(sql)
    if match:
        parse_comment(sql, match, result)
        return

    match = SET_DEFAULT.match(sql)
    if match:
        apply_default(match, result, line)
        return

    match = ADD_IDENTITY.match(sql)
    if match:
        apply_identity(match, result)
        return

    match = OWNED_BY.match(sql)
    if match:
        apply_owned_by(match, result)
        return

    match = ALTER_TABLE.match(sql)
    if match:
        parse_alter_table(sql, match, line, result)
        return

    if is_noise(sql, result.dialect):
        result.skipped += 1
        return

    result.skipped += 1
    result.warnings.append(f"{line}행: 해석하지 않은 문장: {first_line(sql)}")


def parse_enum_values(sql):
    """CREATE TYPE ... AS ENUM (...) 의 값 목록을 꺼낸다."""
    match = re.search(r"AS\s+ENUM\s*\(", sql, re.IGNORECASE)
    if not match:
        return []
    open_index = sql.find("(", match.start())
    close_index = matching_paren(sql, open_index)
    if close_index == -1:
        return []
    inner = sql[open_index + 1 : close_index]
    values = []
    for part in split_top_level(inner):
        text = part.strip()
        literal = re.match(r"^'((?:[^']|'')*)'$", text, re.DOTALL)
        if literal:
            values.append(literal.group(1).replace("''", "'"))
        elif text:
            values.append(text)
    return values


def first_line(sql, limit=90):
    text = " ".join(sql.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def is_noise(sql, dialect):
    upper = sql.strip().upper()
    if dialect == "mysql":
        if any(pattern.match(sql) for pattern in MYSQL_NOISE_PATTERNS):
            return True
        if upper.startswith("CREATE TRIGGER") or upper.startswith("CREATE PROCEDURE") or upper.startswith("CREATE FUNCTION"):
            return True
        if upper.startswith("CREATE TABLE") and re.search(r"\bLIKE\b", upper[:200]):
            return True
    for prefix in PG_NOISE_PREFIXES:
        if upper.startswith(prefix):
            return True
    if upper.startswith("CREATE INDEX") or upper.startswith("COMMENT ON TABLE") or upper.startswith("COMMENT ON COLUMN"):
        return False
    return False


def parse_create_table(sql, match, line, result):
    name_text = match.group("name").strip()
    schema, name = split_object_name(name_text)

    open_index = find_open_paren(sql, match.end("name"))
    if open_index == -1:
        if re.search(r"\bLIKE\b|\bAS\b", sql[match.end("name") :], re.IGNORECASE):
            result.skipped += 1
            result.warnings.append(f"{line}행: CREATE TABLE ... LIKE/AS는 지원하지 않습니다: {name}")
        return

    close_index = matching_paren(sql, open_index)
    if close_index == -1:
        result.warnings.append(f"{line}행: CREATE TABLE 괄호가 닫히지 않았습니다: {name}")
        return

    body = sql[open_index + 1 : close_index]
    tail = sql[close_index + 1 :].strip()
    table = result.table(schema, name, result.dialect, line)
    parse_table_options(tail, table)

    for item in split_top_level(body):
        parse_table_item(item, table, line, result)


def find_open_paren(sql, start):
    quote = None
    for index in range(start, len(sql)):
        char = sql[index]
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ('"', "`"):
            quote = char
            continue
        if char == "(":
            return index
    return -1


def parse_table_options(tail, table):
    if not tail:
        return
    text = re.sub(r"^/\*!.*?\*/\s*", "", tail).strip().rstrip(";").strip()
    if not text:
        return
    for option in split_options(text):
        upper = option.upper()
        comment = re.match(r"^COMMENT\s*=?\s*'((?:[^']|'')*)'$", option, re.IGNORECASE | re.DOTALL)
        if comment:
            table["comment"] = comment.group(1).replace("''", "'")
            continue
        if re.match(r"^AUTO_INCREMENT\s*=", upper) or re.match(r"^AUTO_INCREMENT=", upper):
            continue
        if re.match(r"^(DEFAULT\s+)?(CHARSET|CHARACTER\s+SET|COLLATE)\b", upper) or re.match(
            r"^(ENGINE|ROW_FORMAT|TABLESPACE|WITH|WITHOUT|TABLESPACE|USING)\b", upper
        ):
            table["options"].append(normalize_option(option, table["dialect"]))


def split_options(text):
    parts = []
    buffer = []
    depth = 0
    quote = None
    for char in text:
        if quote:
            buffer.append(char)
            if char == quote:
                quote = None
            continue
        if char in ("'", '"', "`"):
            quote = char
            buffer.append(char)
            continue
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        if char == " " and depth == 0:
            candidate = "".join(buffer).strip()
            if candidate:
                parts.append(candidate)
            buffer = []
            continue
        buffer.append(char)
    candidate = "".join(buffer).strip()
    if candidate:
        parts.append(candidate)

    merged = []
    for part in parts:
        if merged and merged[-1].upper().endswith("="):
            merged[-1] = merged[-1] + part
        else:
            merged.append(part)
    return merged


def normalize_option(option, dialect):
    text = " ".join(option.split())
    if dialect == "mysql":
        text = re.sub(r"^DEFAULT\s+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^CHARSET\s*=\s*", "CHARSET=", text, flags=re.IGNORECASE)
        text = re.sub(r"^COLLATE\s*=\s*", "COLLATE=", text, flags=re.IGNORECASE)
    return text


def parse_table_item(item, table, line, result):
    text = item.strip()
    if not text:
        return

    match = TABLE_CONSTRAINT_START.match(text)
    if match:
        parse_table_constraint(match, table, line, result)
        return

    parse_column(text, table, line, result)


def constraint_columns(body):
    open_index = body.find("(")
    if open_index == -1:
        return []
    close_index = matching_paren(body, open_index)
    if close_index == -1:
        close_index = len(body) - 1
    inner = body[open_index + 1 : close_index]
    columns = []
    for part in split_top_level(inner):
        cleaned = part.strip()
        cleaned = re.sub(r"\s+(ASC|DESC)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+NULLS\s+(FIRST|LAST)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\(\s*\d+\s*\)$", "", cleaned)
        cleaned = re.sub(r"^(COLLATE\s+\S+\s+)", "", cleaned, flags=re.IGNORECASE)
        columns.append(unquote_identifier(cleaned))
    return columns


def normalize_index_column(text, dialect="postgres"):
    """표현식 인덱스 컬럼의 캐스트를 정리한다.

    `lower((email)::text)` -> `lower(email)`
    단순 컬럼은 그대로 둔다.
    """
    value = (text or "").strip()
    if re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", value):
        return value
    if value.startswith("(") and value.endswith(")"):
        pass
    if dialect != "postgres":
        return value
    value = normalize_expression(value, dialect)
    value = re.sub(r"\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", r"\1", value)
    return value


def unquote_identifier(text):
    """따옴표로 감싼 단순 식별자만 벗긴다. 표현식은 그대로 둔다."""
    candidate = (text or "").strip()
    if len(candidate) < 2:
        return candidate
    opener, closer = candidate[0], candidate[-1]
    if opener == closer and opener in ('"', "`"):
        inner = candidate[1:-1]
        if opener * 2 in inner:
            return inner.replace(opener * 2, opener)
        if opener in inner:
            return candidate
        return inner
    if opener == "[" and closer == "]":
        inner = candidate[1:-1]
        if "[" in inner:
            return candidate
        return inner
    return candidate


def parse_table_constraint(match, table, line, result):
    kind = " ".join(match.group("kind").upper().split())
    name = unquote_identifier(match.group("name") or "")
    body = match.group("body") or ""

    if kind.startswith("PRIMARY KEY"):
        add_primary_key(table, name, constraint_columns(body))
        return
    if kind.startswith("UNIQUE"):
        body, inline_name = split_index_name(body)
        add_unique(table, name or inline_name, constraint_columns(body))
        return
    if kind.startswith("FOREIGN KEY"):
        parse_foreign_key(name, body, table, result, line)
        return
    if kind == "CHECK":
        expression = body.strip()
        add_check(table, name, expression)
        return
    if kind.startswith(("KEY", "INDEX", "FULLTEXT", "SPATIAL")):
        body, inline_name = split_index_name(body)
        add_index(
            table,
            name or inline_name,
            constraint_columns(body),
            unique=kind.startswith("UNIQUE"),
            method=kind.split()[0].lower(),
        )
        return

    result.warnings.append(f"{line}행: 알 수 없는 테이블 제약: {first_line(match.group(0))}")


def split_index_name(body):
    """`KEY \\`idx\\` (col)` 형태에서 인덱스 이름을 떼어낸다."""
    text = (body or "").strip()
    if text.startswith("("):
        return text, ""
    match = re.match(r"^(?P<name>[^\s(]+)\s*(?P<rest>\(.*)$", text, re.DOTALL)
    if match:
        return match.group("rest"), unquote_identifier(match.group("name"))
    return text, ""


def parse_foreign_key(name, body, table, result, line=0):
    text = re.sub(r"^FOREIGN\s+KEY\s*", "", body.strip(), flags=re.IGNORECASE)
    match = re.match(
        r"^\((?P<columns>.*?)\)\s*REFERENCES\s+(?P<ref>[^\s(]+)\s*\((?P<ref_columns>.*?)\)(?P<tail>.*)$",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        result.warnings.append(f"{line}행: FOREIGN KEY를 해석하지 못했습니다: {first_line(body)}")
        return
    columns = [unquote_identifier(part) for part in split_top_level(match.group("columns"))]
    ref_schema, ref_table = split_object_name(match.group("ref"))
    ref_columns = [unquote_identifier(part) for part in split_top_level(match.group("ref_columns"))]
    tail = match.group("tail") or ""
    on_delete = extract_action(tail, "DELETE")
    on_update = extract_action(tail, "UPDATE")
    deferrable = extract_deferrable(tail)
    add_foreign_key(table, name, columns, ref_schema, ref_table, ref_columns, on_delete, on_update, deferrable)


def extract_action(tail, action):
    match = re.search(
        rf"ON\s+{action}\s+(CASCADE|RESTRICT|SET\s+NULL|SET\s+DEFAULT|NO\s+ACTION)",
        tail,
        re.IGNORECASE,
    )
    return " ".join(match.group(1).upper().split()) if match else ""


def extract_deferrable(tail):
    if re.search(r"\bDEFERRABLE\b", tail, re.IGNORECASE):
        text = "DEFERRABLE"
        if re.search(r"\bINITIALLY\s+DEFERRED\b", tail, re.IGNORECASE):
            text += " INITIALLY DEFERRED"
        return text
    return ""


def parse_column(text, table, line, result):
    tokens = first_tokens(text, 2)
    if not tokens:
        return
    name = unquote(tokens[0])
    rest = text[len(tokens[0]) :].lstrip()
    if not rest:
        result.warnings.append(f"{line}행: 컬럼 타입이 없습니다: {name}")
        return

    column = new_column(name)
    type_part, constraint_part = split_column_type(rest)
    column["type"] = normalize_type(type_part, table["dialect"])

    parse_column_constraints(constraint_part, column, table, line, result)

    existing = find_column(table, name)
    if existing is not None:
        table["columns"][table["columns"].index(existing)] = column
    else:
        table["columns"].append(column)


def first_tokens(text, count):
    tokens = []
    index = 0
    length = len(text)
    while index < length and len(tokens) < count:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char in ('"', "`", "["):
            closer = "]" if char == "[" else char
            cursor = index + 1
            while cursor < length:
                if text[cursor] == closer:
                    cursor += 1
                    break
                cursor += 1
            tokens.append(text[index:cursor])
            index = cursor
            continue
        cursor = index
        while cursor < length and not text[cursor].isspace():
            cursor += 1
        tokens.append(text[index:cursor])
        index = cursor
    return tokens


def split_column_type(rest):
    text = rest.strip()
    if text.startswith("("):
        close = matching_paren(text, 0)
        if close != -1:
            return text[: close + 1], text[close + 1 :].strip()
    tokens = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "(":
            close = matching_paren(text, index)
            if close == -1:
                close = length - 1
            tokens.append(text[index : close + 1])
            index = close + 1
            continue
        if char.isspace():
            index += 1
            continue
        cursor = index
        while cursor < length and not text[cursor].isspace() and text[cursor] != "(":
            cursor += 1
        tokens.append(text[index:cursor])
        index = cursor

    stop = len(tokens)
    for position, token in enumerate(tokens):
        candidate = token.upper()
        if candidate in ("NOT", "NULL", "PRIMARY", "UNIQUE", "DEFAULT", "REFERENCES", "CHECK",
                         "COLLATE", "AUTO_INCREMENT", "AUTOINCREMENT", "GENERATED",
                         "COMMENT", "CONSTRAINT"):
            stop = position
            break
        if candidate == "ON" and position + 1 < len(tokens) and tokens[position + 1].upper() == "UPDATE":
            stop = position
            break
        if candidate == "CHARACTER" and position + 1 < len(tokens) and tokens[position + 1].upper() == "SET":
            stop = position
            break
        if candidate == "CHARSET":
            stop = position
            break

    type_tokens = tokens[:stop]
    constraint_tokens = tokens[stop:]
    return " ".join(type_tokens), " ".join(constraint_tokens)


def parse_column_constraints(text, column, table, line, result):
    if not text:
        return

    if re.search(r"\bAUTO_INCREMENT\b|\bAUTOINCREMENT\b", text, re.IGNORECASE):
        column["auto_increment"] = True

    identity = re.search(
        r"GENERATED\s+(ALWAYS|BY\s+DEFAULT)\s+AS\s+IDENTITY\s*(\([^)]*\))?",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if identity:
        column["identity"] = " ".join(identity.group(1).upper().split())
        body = identity.group(2) or ""
        sequence = re.search(r"SEQUENCE\s+NAME\s+([^\s,)]+)", body, re.IGNORECASE)
        if sequence:
            column["identity_sequence"] = sequence.group(1)
        text = text[: identity.start()] + text[identity.end() :]

    generated = re.search(
        r"GENERATED\s+ALWAYS\s+AS\s*\((?P<expression>.*?)\)\s*(?P<storage>STORED|VIRTUAL)?",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if generated and not identity:
        column["generated"] = normalize_expression(generated.group("expression"), table["dialect"])
        text = text[: generated.start()] + text[generated.end() :]

    if re.search(r"\bNOT\s+NULL\b", text, re.IGNORECASE):
        column["nullable"] = False
    if re.search(r"\bPRIMARY\s+KEY\b", text, re.IGNORECASE):
        column["primary_key"] = True
        column["nullable"] = False

    unique = re.search(r"\bUNIQUE(?:\s+KEY)?\b", text, re.IGNORECASE)
    if unique:
        column["unique"] = True

    default = extract_keyword_value(text, "DEFAULT")
    if default:
        column["default"] = normalize_expression(default, table["dialect"])

    comment = re.search(r"\bCOMMENT\s+'((?:[^']|'')*)'", text, re.IGNORECASE | re.DOTALL)
    if comment:
        column["comment"] = comment.group(1).replace("''", "'")

    collate = re.search(r"\bCOLLATE\s+([^\s,)]+)", text, re.IGNORECASE)
    if collate:
        column["collate"] = collate.group(1)

    charset = re.search(r"\b(?:CHARACTER\s+SET|CHARSET)\s+([^\s,)]+)", text, re.IGNORECASE)
    if charset:
        column["charset"] = charset.group(1)

    on_update = re.search(
        r"\bON\s+UPDATE\s+(CURRENT_TIMESTAMP(?:\(\))?|[A-Za-z_][\w.]*(?:\([^)]*\))?)",
        text,
        re.IGNORECASE,
    )
    if on_update:
        column["on_update"] = on_update.group(1)

    if re.search(r"\bUNSIGNED\b", text, re.IGNORECASE):
        column["unsigned"] = True
    if re.search(r"\bZEROFILL\b", text, re.IGNORECASE):
        column["zerofill"] = True

    check = re.search(r"\bCHECK\s*(\(.*\))$", text, re.IGNORECASE | re.DOTALL)
    if check:
        column["check"] = normalize_expression(check.group(1), table["dialect"])

    references = re.search(
        r"\bREFERENCES\s+([^\s(]+)\s*\(([^)]*)\)(?P<tail>.*)$",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if references:
        ref_schema, ref_table = split_object_name(references.group(1))
        tail = references.group("tail") or ""
        tail = re.split(r"\b(?:CHECK|UNIQUE|PRIMARY|DEFAULT|NOT\s+NULL)\b", tail, flags=re.IGNORECASE)[0]
        column["references"] = {
            "schema": ref_schema,
            "table": ref_table,
            "columns": [unquote_identifier(part) for part in split_top_level(references.group(2))],
            "on_delete": extract_action(tail, "DELETE"),
            "on_update": extract_action(tail, "UPDATE"),
            "deferrable": extract_deferrable(tail),
        }

    for keyword, label in (
        ("DEFERRABLE", "deferrable"),
        ("INITIALLY", "initially"),
    ):
        if re.search(rf"\b{keyword}\b", text, re.IGNORECASE) and label == "deferrable":
            column["raw_extra"].append("DEFERRABLE")


def extract_keyword_value(text, keyword):
    pattern = re.compile(rf"\b{keyword}\b\s+", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return ""
    index = match.end()
    depth = 0
    quote = None
    cursor = index
    length = len(text)
    while cursor < length:
        char = text[cursor]
        if quote:
            if char == "\\" and quote == "'" and cursor + 1 < length:
                cursor += 2
                continue
            if char == quote:
                if cursor + 1 < length and text[cursor + 1] == quote:
                    cursor += 2
                    continue
                quote = None
            cursor += 1
            continue
        if char in ("'", '"'):
            quote = char
            cursor += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            if char.isspace():
                remainder = text[cursor:].strip()
                if re.match(r"^(NOT|NULL|PRIMARY|UNIQUE|REFERENCES|CHECK|COLLATE|COMMENT|"
                            r"AUTO_INCREMENT|GENERATED|ON)\b", remainder, re.IGNORECASE):
                    break
                cursor += 1
                continue
        cursor += 1
    return text[index:cursor].strip()


def parse_create_index(sql, match, result):
    name = unquote(match.group("name"))
    schema, table_name = split_object_name(match.group("table"))
    unique = bool(match.group("unique"))
    rest = (match.group("rest") or "").strip()
    if rest.startswith("USING"):
        rest = rest[5:].strip()

    method = ""
    method_match = re.match(r"^(BTREE|HASH|GIST|GIN|SPGIST|BRIN|RTREE|FULLTEXT|SPATIAL)\b", rest, re.IGNORECASE)
    if method_match:
        method = method_match.group(1).upper()
        rest = rest[method_match.end() :].strip()

    open_index = rest.find("(")
    if open_index == -1:
        result.warnings.append(f"INDEX 컬럼을 찾지 못했습니다: {name}")
        return
    close_index = matching_paren(rest, open_index)
    if close_index == -1:
        close_index = len(rest) - 1
    inner = rest[open_index + 1 : close_index]
    columns = [normalize_index_column(item, result.dialect) for item in constraint_columns(f"({inner})")]
    tail = rest[close_index + 1 :]
    where = ""
    where_match = re.search(r"\bWHERE\s+(.+)$", tail, re.IGNORECASE | re.DOTALL)
    if where_match:
        where = normalize_expression(where_match.group(1), result.dialect)

    from .model import table_key

    key = table_key(schema, table_name)
    table = result.tables.get(key)
    if table is None:
        table = result.table(schema, table_name, result.dialect, 0)
    add_index(table, name, columns, unique=unique, method=method, where=where)


def parse_comment(sql, match, result):
    kind = match.group("kind").upper()
    target = match.group("target").strip()
    value = match.group("value").strip()

    literal = re.match(r"^'((?:[^']|'')*)'$", value, re.DOTALL)
    if literal:
        value = literal.group(1).replace("''", "'")
    elif value.upper() == "NULL":
        value = ""

    if kind == "TABLE":
        schema, name = split_object_name(target)
        table = get_or_create(result, schema, name)
        table["comment"] = value
        return

    parts = split_qualified(target)
    if len(parts) < 2:
        result.warnings.append(f"{kind} 주석 대상을 해석하지 못했습니다: {target}")
        return
    column_name = unquote(parts[-1])
    table_parts = parts[:-1]
    schema = unquote(table_parts[-2]) if len(table_parts) >= 2 else ""
    name = unquote(table_parts[-1])
    table = get_or_create(result, schema, name)
    column = find_column(table, column_name)
    if column is None:
        column = new_column(column_name)
        table["columns"].append(column)
    column["comment"] = value


def get_or_create(result, schema, name):
    from .model import table_key

    key = table_key(schema, name)
    if key in result.tables:
        return result.tables[key]
    existing = None
    for table in result.tables.values():
        if simple_name(table["name"]) == simple_name(name) and (
            not schema or not table["schema"] or simple_name(table["schema"]) == simple_name(schema)
        ):
            existing = table
            break
    if existing is not None:
        return existing
    table = result.table(schema or "", name, result.dialect, 0)
    result.tables[table_key(schema, name)] = table
    return table


def apply_default(match, result, line):
    schema, name = split_object_name(match.group("table"))
    column_name = unquote(match.group("column"))
    value = normalize_expression(match.group("value"), result.dialect)
    table = find_table(result, schema, name)
    if table is None:
        result.warnings.append(f"{line}행: DEFAULT 대상 테이블을 찾지 못했습니다: {match.group('table')}")
        return
    column = find_column(table, column_name)
    if column is None:
        result.warnings.append(f"{line}행: DEFAULT 대상 컬럼을 찾지 못했습니다: {column_name}")
        return
    column["default"] = value


def apply_identity(match, result):
    schema, name = split_object_name(match.group("table"))
    column_name = unquote(match.group("column"))
    table = find_table(result, schema, name)
    if table is None:
        return
    column = find_column(table, column_name)
    if column is None:
        return
    column["identity"] = " ".join(match.group("kind").upper().split())
    body = match.group("body") or ""
    sequence = re.search(r"SEQUENCE\s+NAME\s+([^\s,)]+)", body, re.IGNORECASE)
    if sequence:
        column["identity_sequence"] = sequence.group(1)


def apply_owned_by(match, result):
    table_name = unquote(match.group("table"))
    column_name = unquote(match.group("column"))
    for table in result.tables.values():
        if simple_name(table["name"]) == simple_name(table_name):
            column = find_column(table, column_name)
            if column is not None and not column["identity"]:
                column["auto_increment"] = True
            return


def find_table(result, schema, name):
    from .model import table_key

    key = table_key(schema, name)
    if key in result.tables:
        return result.tables[key]
    for table in result.tables.values():
        if simple_name(table["name"]) == simple_name(name):
            return table
    return None


def parse_alter_table(sql, match, line, result):
    schema, name = split_object_name(match.group("table"))
    rest = (match.group("rest") or "").strip()
    table = find_table(result, schema, name)
    if table is None:
        if re.match(r"^(OWNER\s+TO|ALTER\s+COLUMN.*(SET\s+STATISTICS|SET\s+STORAGE))", rest, re.IGNORECASE | re.DOTALL):
            result.skipped += 1
            return
        result.warnings.append(f"{line}행: ALTER TABLE 대상 테이블이 없습니다: {match.group('table')}")
        result.skipped += 1
        return

    for action in split_top_level(rest):
        parse_alter_action(action.strip(), table, line, result)


def parse_alter_action(action, table, line, result):
    if not action:
        return
    if PG_ALTER_OWNER.match(action):
        return
    if re.match(r"^(ALTER\s+COLUMN\s+\S+\s+)?(SET\s+STATISTICS|SET\s+STORAGE|RESET\s+\(|SET\s+\(|RESET\s+STORAGE)", action, re.IGNORECASE):
        return
    if re.match(r"^ENABLE\s+ROW\s+LEVEL\s+SECURITY$|^DISABLE\s+ROW\s+LEVEL\s+SECURITY$|^FORCE\s+ROW\s+LEVEL\s+SECURITY$", action, re.IGNORECASE):
        return
    if re.match(r"^(REPLICA\s+IDENTITY|CLUSTER\s+ON|SET\s+WITHOUT\s+CLUSTER|SET\s+WITH\s+OIDS)", action, re.IGNORECASE):
        return

    match = PG_ALTER_ADD_CONSTRAINT.match(action)
    if match:
        parse_added_constraint(match.group("name"), match.group("body"), table, line, result)
        return

    match = PG_ALTER_ADD_NO_NAME.match(action)
    if match:
        parse_added_constraint("", match.group("body"), table, line, result)
        return

    match = PG_ALTER_ADD_COLUMN.match(action)
    if match:
        body = match.group("body")
        if body.upper().startswith("CONSTRAINT"):
            return
        parse_column(body, table, line, result)
        return

    match = PG_ALTER_ALTER_COLUMN.match(action)
    if match:
        parse_alter_column(match.group("column"), match.group("body"), table, line, result)
        return

    if re.match(r"^DROP\s+CONSTRAINT\b", action, re.IGNORECASE):
        return
    if re.match(r"^DROP\s+(COLUMN\s+)?", action, re.IGNORECASE):
        result.warnings.append(f"{line}행: DROP COLUMN은 반영하지 않았습니다: {first_line(action)}")
        return
    if re.match(r"^OWNER\s+TO\b", action, re.IGNORECASE):
        return
    if re.match(r"^RENAME\b", action, re.IGNORECASE):
        result.warnings.append(f"{line}행: RENAME은 반영하지 않았습니다: {first_line(action)}")
        return
    if re.match(r"^ADD\s+(KEY|INDEX|UNIQUE\s+KEY|FULLTEXT|SPATIAL)", action, re.IGNORECASE):
        match = re.match(r"^ADD\s+(?P<kind>UNIQUE\s+KEY|UNIQUE\s+INDEX|KEY|INDEX|FULLTEXT(?:\s+KEY)?|SPATIAL(?:\s+KEY)?)\s*(?P<rest>.*)$", action, re.IGNORECASE | re.DOTALL)
        if match:
            rest = match.group("rest").strip()
            name_match = re.match(r"^(?P<name>[^\s(]+)\s*(?P<body>\(.*)$", rest, re.DOTALL)
            if name_match:
                add_index(
                    table,
                    unquote(name_match.group("name")),
                    constraint_columns(name_match.group("body")),
                    unique=match.group("kind").upper().startswith("UNIQUE"),
                )
                return
    result.warnings.append(f"{line}행: 해석하지 않은 ALTER TABLE 동작: {first_line(action)}")


def parse_added_constraint(name, body, table, line, result):
    text = body.strip()
    upper = text.upper()
    if upper.startswith("PRIMARY KEY"):
        add_primary_key(table, name, constraint_columns(text))
        return
    if upper.startswith("UNIQUE"):
        add_unique(table, name, constraint_columns(text))
        return
    if upper.startswith("FOREIGN KEY"):
        parse_foreign_key(name, text, table, result, line)
        return
    if upper.startswith("CHECK"):
        add_check(table, name, text)
        return
    result.warnings.append(f"{line}행: 알 수 없는 제약: {first_line(text)}")


def parse_alter_column(column_name, body, table, line, result):
    column = find_column(table, unquote(column_name))
    if column is None:
        result.warnings.append(f"{line}행: ALTER COLUMN 대상이 없습니다: {column_name}")
        return
    text = body.strip()
    upper = text.upper()
    if upper.startswith("SET DEFAULT"):
        column["default"] = normalize_expression(text[len("SET DEFAULT") :], table["dialect"])
        return
    if upper.startswith("DROP DEFAULT"):
        column["default"] = ""
        return
    if upper.startswith("SET NOT NULL"):
        column["nullable"] = False
        return
    if upper.startswith("DROP NOT NULL"):
        column["nullable"] = True
        return
    if upper.startswith("TYPE ") or upper.startswith("SET DATA TYPE "):
        type_text = re.sub(r"^(TYPE|SET\s+DATA\s+TYPE)\s+", "", text, flags=re.IGNORECASE)
        type_text = re.split(r"\bUSING\b", type_text, flags=re.IGNORECASE)[0]
        column["type"] = normalize_type(type_text, table["dialect"])
        return
    if re.match(r"^(SET\s+STATISTICS|SET\s+STORAGE|RESET\s+\(|SET\s+\()", text, re.IGNORECASE):
        return
    result.warnings.append(f"{line}행: 해석하지 않은 ALTER COLUMN: {first_line(text)}")


def finalize(result):
    for table in result.tables.values():
        for column in table["columns"]:
            if column["primary_key"] and table["primary_key"] is None:
                add_primary_key(table, "", [column["name"]])
            reference = column["references"]
            if reference:
                add_foreign_key(
                    table,
                    "",
                    [column["name"]],
                    reference["schema"],
                    reference["table"],
                    reference["columns"],
                    reference["on_delete"],
                    reference["on_update"],
                    reference["deferrable"],
                )
            if column["unique"]:
                add_unique(table, column["unique_name"], [column["name"]])
        apply_mysql_serial(table)


def apply_mysql_serial(table):
    """MySQL의 AUTO_INCREMENT 정수 PK를 serial 계열로 바꿀 수 있게 표시한다."""
    for column in table["columns"]:
        if column["auto_increment"]:
            column["identity"] = "AUTO_INCREMENT"
