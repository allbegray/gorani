"""변환 검토 md. 빠진 객체·이름 변경·경고를 사람이 확인할 수 있게 모은다."""

from .model import qualified_name, table_key


def build_review(result, options, files, generated_at):
    lines = ["# DDL 변환 검토", ""]
    lines.append(
        f"입력 {len(files)}개 파일, 방언 `{result.dialect}`, 생성 시각 `{generated_at}`"
    )
    lines.append("")

    lines.append("## 요약")
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("| --- | --- |")
    tables = sorted(result.tables.values(), key=lambda item: table_key(item["schema"], item["name"]))
    lines.append(f"| 테이블 | {len(tables)} |")
    lines.append(f"| 컬럼 | {sum(len(table['columns']) for table in tables)} |")
    lines.append(f"| 외래 키 | {sum(len(table['foreign_keys']) for table in tables)} |")
    lines.append(f"| 인덱스 | {sum(len(table['indexes']) for table in tables)} |")
    lines.append(f"| CHECK | {sum(len(table['checks']) for table in tables)} |")
    lines.append(f"| UNIQUE | {sum(len(table['uniques']) for table in tables)} |")
    lines.append(f"| 경고 | {len(result.warnings)} |")
    lines.append(f"| 건너뛴 문장 | {result.skipped} |")
    lines.append("")

    renamed = renamed_items(tables, options)
    if renamed:
        lines.append("## 바뀐 이름")
        lines.append("")
        lines.append("dump가 자동으로 만든 제약·인덱스 이름을 사람이 읽기 좋은 이름으로 바꿨습니다.")
        lines.append("")
        lines.append("| 테이블 | 종류 | 원본 | 변환 |")
        lines.append("| --- | --- | --- | --- |")
        for row in renamed:
            lines.append(f"| `{row[0]}` | {row[1]} | `{row[2]}` | `{row[3]}` |")
        lines.append("")

    excluded = excluded_objects(result, options)
    if excluded:
        lines.append("## 변환에서 빠진 객체")
        lines.append("")
        lines.append("다음 객체는 dump에 있었지만 이 변환의 결과 DDL에는 들어가지 않았습니다. 필요하면 직접 옮깁니다.")
        lines.append("")
        for item in excluded:
            lines.append(f"- {item}")
        lines.append("")

    if result.warnings:
        lines.append("## 경고")
        lines.append("")
        lines.append("해석하지 못했거나 사람이 확인해야 하는 문장입니다.")
        lines.append("")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## 확인할 것")
    lines.append("")
    lines.append("- 변환 결과 DDL을 실제 DB의 빈 스키마에 실행해 오류가 없는지 확인합니다.")
    lines.append("- 컬럼 수·제약 수가 원본과 같은지 `--model-out`의 `summary`로 대조합니다.")
    lines.append("- ENUM·시퀀스·함수·트리거처럼 테이블 밖 객체가 필요하면 별도로 옮깁니다.")
    lines.append("")
    return "\n".join(lines)


def renamed_items(tables, options):
    from .render_sql import build_name, is_dump_name

    rows = []
    if not options.rename_constraints:
        return rows
    for table in tables:
        name = qualified_name(table["schema"], table["name"], options.dialect, options.strip_schema)
        primary_key = table["primary_key"]
        if primary_key and len(primary_key["columns"]) > 1 and primary_key["name"]:
            if is_dump_name(primary_key["name"], table):
                new = build_name("pk", table["name"], primary_key["columns"])
                rows.append([name, "PRIMARY KEY", primary_key["name"], new])
        for unique in table["uniques"]:
            if not unique["name"]:
                continue
            if is_dump_name(unique["name"], table):
                new = build_name("uq", table["name"], unique["columns"])
                rows.append([name, "UNIQUE", unique["name"], new])
        for check in table["checks"]:
            if not check["name"]:
                continue
            if is_dump_name(check["name"], table):
                columns = [column["name"] for column in table["columns"] if column["name"] in check["expression"]]
                new = build_name("ck", table["name"], columns[:2])
                rows.append([name, "CHECK", check["name"], new])
        for foreign_key in table["foreign_keys"]:
            if not foreign_key["name"]:
                continue
            if is_dump_name(foreign_key["name"], table):
                new = build_name("fk", table["name"], foreign_key["columns"])
                rows.append([name, "FOREIGN KEY", foreign_key["name"], new])
        for index in table["indexes"]:
            if not index["name"]:
                continue
            if is_dump_name(index["name"], table):
                new = build_name("uq" if index["unique"] else "idx", table["name"], index["columns"])
                rows.append([name, "INDEX", index["name"], new])
    return rows


def excluded_objects(result, options):
    items = []
    enum_names = [item["name"] if isinstance(item, dict) else item for item in result.types]
    if enum_names and not (options.dialect == "postgres" and options.enums):
        items.append(f"ENUM 타입 {len(enum_names)}개: {', '.join(enum_names[:5])}")
    if result.sequences:
        items.append(f"시퀀스 {len(result.sequences)}개 (serial 컬럼이면 결과 DDL에 자동 포함)")
    if result.schemas:
        items.append(f"CREATE SCHEMA {len(result.schemas)}개: {', '.join(result.schemas[:5])}")
    if result.skipped:
        items.append(f"그 밖의 문장 {result.skipped}개 (SET, OWNER, GRANT, 데이터 등)")
    return items
