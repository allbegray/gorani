"""공유 상수."""

DIALECTS = ["postgres", "mysql", "sqlite", "mssql", "oracle"]
OUTPUT_FORMATS = ("md", "xlsx", "html")
DEFAULT_FORMATS = "xlsx,md,html"
SYSTEM_TABLE_NAMES = {"msreplication_options", "sysdiagrams"}
SYSTEM_TABLE_PREFIXES = ("spt_", "trace_xe_")
SYSTEM_SCHEMAS = {"information_schema", "sys", "mysql", "performance_schema"}

SCHEMA_VERSION = 1
