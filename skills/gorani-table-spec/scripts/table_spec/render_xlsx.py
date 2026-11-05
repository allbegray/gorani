"""테이블 명세서를 XLSX로 렌더링한다. openpyxl은 이 모듈의 함수 안에서만 import한다."""

import sys

from .render_md import table_label


def write_xlsx(path, model):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        sys.exit(
            "xlsx를 만들려면 openpyxl이 필요합니다. 스킬의 도구 설치 원칙에 따라 설치한 뒤 다시 시도하세요."
        )

    meta = model.get("meta", {})
    summary_counts = model.get("summary", {})
    tables = model.get("tables", [])
    warnings = model.get("warnings", [])
    data = {
        "project": meta.get("project", ""),
        "generated_at": meta.get("generated_at", ""),
        "dialects": meta.get("dialects") or [],
        "source_label": meta.get("source_label", "-"),
        "column_count": summary_counts.get("columns", 0),
        "fk_count": summary_counts.get("foreign_keys", 0),
        "index_count": summary_counts.get("indexes", 0),
        "warnings": warnings,
    }

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(size=14, bold=True)
    section_font = Font(bold=True)
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style_header(ws, widths):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        for index, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(index)].width = width
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def write_rows(ws, rows, widths):
        ws.append(rows[0])
        style_header(ws, widths)
        for row in rows[1:]:
            ws.append(row)
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(widths)):
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

    workbook = Workbook()
    summary = workbook.active
    summary.title = "요약"
    summary["A1"] = "테이블 명세서"
    summary["A1"].font = title_font
    summary.merge_cells("A1:D1")
    summary_rows = [
        ("프로젝트", data["project"] or "-"),
        ("생성 시각", data["generated_at"]),
        ("SQL 방언", ", ".join(data["dialects"]) or "-"),
        ("원본", data.get("source_label", "-")),
        ("테이블", len(tables)),
        ("컬럼", data["column_count"]),
        ("관계(FK)", data["fk_count"]),
        ("인덱스", data["index_count"]),
        ("파싱 경고", len(data["warnings"])),
    ]
    for index, (label, value) in enumerate(summary_rows, start=3):
        summary.cell(row=index, column=1, value=label).font = section_font
        summary.cell(row=index, column=2, value=value)
    note_row = len(summary_rows) + 5
    summary.cell(row=note_row, column=1, value="읽는 법").font = section_font
    summary.cell(row=note_row + 1, column=1, value="PK=기본키, FK=외래키, UNIQUE=단일 컬럼 유니크, NOT NULL=필수")
    summary.cell(row=note_row + 2, column=1, value="관계·인덱스는 각 시트에서 확인합니다.")
    summary.column_dimensions["A"].width = 24
    summary.column_dimensions["B"].width = 60

    table_rows = [["No", "스키마", "테이블", "설명", "컬럼", "PK", "FK", "인덱스"]]
    for index, table in enumerate(tables, start=1):
        table_rows.append(
            [
                index,
                table["schema"],
                table["name"],
                table["description"],
                len(table["columns"]),
                ", ".join(table["primary_key"]),
                len(table["foreign_keys"]),
                len(table["indexes"]),
            ]
        )
    write_rows(workbook.create_sheet("테이블 목록"), table_rows, [6, 14, 30, 46, 8, 20, 8, 8])

    column_rows = [
        [
            "No",
            "스키마",
            "테이블",
            "테이블 설명",
            "순서",
            "컬럼",
            "데이터 타입",
            "길이/정밀도",
            "PK",
            "FK",
            "UNIQUE",
            "NOT NULL",
            "DEFAULT",
            "설명",
            "비고",
        ]
    ]
    number = 0
    for table in tables:
        for index, column in enumerate(table["columns"], start=1):
            number += 1
            column_rows.append(
                [
                    number,
                    table["schema"],
                    table["name"],
                    table["description"],
                    index,
                    column["name"],
                    column["data_type"],
                    column["length"],
                    "Y" if column["primary_key"] else "",
                    "Y" if column["references"] else "",
                    "Y" if column["unique"] else "",
                    "Y" if not column["nullable"] else "",
                    column["default"],
                    column["comment"],
                    column["note"],
                ]
            )
    write_rows(
        workbook.create_sheet("컬럼 명세"),
        column_rows,
        [6, 14, 30, 46, 7, 24, 22, 14, 6, 6, 9, 10, 24, 46, 24],
    )

    relation_rows = [["FK", "자식 테이블", "자식 컬럼", "부모 테이블", "부모 컬럼", "ON DELETE", "ON UPDATE"]]
    for table in tables:
        for foreign_key in table["foreign_keys"]:
            ref_table = (
                f"{foreign_key['ref_schema']}.{foreign_key['ref_table']}"
                if foreign_key["ref_schema"]
                else foreign_key["ref_table"]
            )
            relation_rows.append(
                [
                    foreign_key["name"],
                    table_label(table),
                    ", ".join(foreign_key["columns"]),
                    ref_table,
                    ", ".join(foreign_key["ref_columns"]),
                    foreign_key["on_delete"],
                    foreign_key["on_update"],
                ]
            )
    write_rows(workbook.create_sheet("관계"), relation_rows, [28, 34, 28, 34, 28, 18, 18])

    index_rows = [["테이블", "인덱스", "UNIQUE", "컬럼"]]
    for table in tables:
        for index in table["indexes"]:
            index_rows.append(
                [
                    table_label(table),
                    index["name"],
                    "Y" if index["unique"] else "",
                    ", ".join(index["columns"]),
                ]
            )
    write_rows(workbook.create_sheet("인덱스"), index_rows, [34, 34, 9, 60])

    warning_rows = [["파일", "메시지"]]
    for warning in warnings:
        warning_path = warning.split(": ", 1)[0] if ": " in warning else ""
        warning_rows.append([warning_path, warning])
    if len(warning_rows) == 1:
        warning_rows.append(["-", "없음"])
    write_rows(workbook.create_sheet("파싱 메모"), warning_rows, [60, 100])

    workbook.save(path)
