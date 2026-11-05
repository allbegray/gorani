"""테이블 명세서를 Markdown으로 렌더링한다."""


def md_cell(value):
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ") or "-"


def table_label(table):
    return f"{table['schema']}.{table['name']}" if table["schema"] else table["name"]


def build_markdown(model):
    meta = model.get("meta", {})
    summary = model.get("summary", {})
    tables = model.get("tables", [])
    warnings = model.get("warnings", [])
    project = meta.get("project", "")
    generated_at = meta.get("generated_at", "")
    source_label = meta.get("source_label", "")
    dialects = meta.get("dialects") or []
    source = meta.get("source", "")

    lines = [
        "# 테이블 명세서",
        "",
        f"- 프로젝트: {project or '-'}",
        f"- 생성 시각: {generated_at}",
        f"- SQL 방언: {', '.join(dialects) or '-'}",
        f"- 원본: {source_label or '-'}",
        f"- 테이블: {len(tables)}",
        f"- 컬럼: {summary.get('columns', 0)}",
        f"- 관계: {summary.get('foreign_keys', 0)}",
        f"- 인덱스: {summary.get('indexes', 0)}",
        "",
        "> 이 문서는 DB에서 조회한 스키마를 기준으로 생성했습니다. 조회 시점 이후 변경될 수 있습니다."
        if source == "database"
        else "> 이 문서는 SQL DDL을 기준으로 생성했습니다. 런타임 DB 상태와 다를 수 있습니다.",
        "",
        "## 테이블 목록",
        "",
        "| No | 스키마 | 테이블 | 설명 | 컬럼 | PK | FK | 인덱스 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, table in enumerate(tables, start=1):
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
    for table in tables:
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
    if warnings:
        lines += ["", "## 파싱 메모", ""]
        for warning in warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines).rstrip() + "\n"
