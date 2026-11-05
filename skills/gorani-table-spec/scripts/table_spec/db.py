"""SQLAlchemy 실제 DB 입력 어댑터.

SQLAlchemy와 DB 드라이버는 introspect_db 안에서만 import한다. DB 모드를 쓰지
않으면 SQLAlchemy가 없어도 된다.
"""

import re
import sys

from .constants import SYSTEM_SCHEMAS, SYSTEM_TABLE_NAMES, SYSTEM_TABLE_PREFIXES
from .model import add_foreign_key, add_index, add_unique, new_column, new_table, split_type, table_key


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
