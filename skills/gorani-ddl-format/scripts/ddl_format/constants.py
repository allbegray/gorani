"""공통 상수."""

SCHEMA_VERSION = 1

DIALECTS = ("postgres", "mysql", "sqlite", "mssql", "oracle")
DEFAULT_DIALECT = "auto"

OUTPUT_FORMATS = ("sql", "review")
DEFAULT_FORMATS = "sql,review"
