"""XLSX 렌더러. 유일하게 openpyxl을 사용하는 모듈이다."""

import sys

from .constants import REVIEW_QUESTIONS
from .model import bool_label, table_label


def write_xlsx(path, model):
    meta = model["meta"]
    pages = model["pages"]
    summary_counts = model["summary"]
    depth_count = summary_counts["depth"]
    warnings = model["warnings"]
    standards = model["standards"]
    api_only = model["api_only"]
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        sys.exit(
            "xlsx를 만들려면 openpyxl이 필요합니다. 스킬의 도구 설치 원칙에 따라 설치한 뒤 다시 시도하세요."
        )

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(size=16, bold=True)
    section_font = Font(bold=True)
    group_fills = [
        PatternFill("solid", fgColor="D9E1F2"),
        PatternFill("solid", fgColor="E2EFDA"),
        PatternFill("solid", fgColor="FFF2CC"),
        PatternFill("solid", fgColor="E4DFEC"),
        PatternFill("solid", fgColor="FCE4D6"),
        PatternFill("solid", fgColor="DDEBF7"),
    ]
    active_fill = PatternFill("solid", fgColor="C6E0B4")
    planned_fill = PatternFill("solid", fgColor="FFE699")
    deprecated_fill = PatternFill("solid", fgColor="D9D9D9")
    api_fill = PatternFill("solid", fgColor="E4DFEC")
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style_header(ws, widths, columns):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        for index, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(index)].width = width
        ws.freeze_panes = "A2"

    def append_row(ws, values):
        ws.append(values)
        row = ws.max_row
        for cell in ws[row]:
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    workbook = Workbook()
    summary = workbook.active
    summary.title = "요약"
    summary.sheet_properties.tabColor = "1F3864"
    summary["A1"] = f"사이트 구조도 — {meta['site']}"
    summary["A1"].font = title_font
    summary.merge_cells("A1:D1")
    summary["A3"] = "기본 정보"
    summary["A3"].font = section_font
    counts = summary_counts["status"]
    rows = [
        ("사이트", meta["site"]),
        ("기준 URL", meta["base_url"] or "-"),
        ("검사 시점", meta["inspected_at"] or "-"),
        ("수집 기준", meta["source"] or "-"),
        ("적용 기준", meta["standard"] or "-"),
        ("검사 역할", ", ".join(meta["roles"]) or "-"),
        ("검사 화면 폭", ", ".join(meta["viewports"]) or "-"),
        ("Depth 규칙", f"메뉴 성격의 depth만 사용. 최소 2Depth, 최대 3Depth (KRDS 메인 메뉴 기준). 현재 {depth_count}Depth"),
        ("수집 방식", "에이전트 화면 확인 + 선택적 Playwright"),
        ("계층 기준", "메뉴 계층 우선, 3Depth 초과는 상세·탭·액션으로 분리"),
        ("화면 수", summary_counts["pages"]),
        ("활성/계획/폐기", f"{counts.get('active', 0)} / {counts.get('planned', 0)} / {counts.get('deprecated', 0)}"),
        ("내비게이션 그룹", summary_counts["menu_groups"]),
        ("API 매핑", summary_counts["api_mappings"]),
        ("API only", len(api_only)),
        ("표준 근거", len(standards)),
        ("검토 메모", len(warnings)),
        ("검토 상태", meta["review_status"] or "초안 — 검토 필요"),
    ]
    for index, (label, value) in enumerate(rows, start=4):
        summary.cell(row=index, column=1, value=label).font = section_font
        summary.cell(row=index, column=2, value=value)
    start = len(rows) + 6
    summary.cell(row=start, column=1, value="시트 구성").font = section_font
    sheet_notes = [
        ("사이트 구조", "실제 메뉴 계층을 Depth 컬럼으로 표시"),
        ("화면 목록", "화면별 URL·역할·노출·상태·스크린샷·API"),
        ("API 매핑", "화면과 API 호출의 연결"),
        ("API only", "화면 없이 API만 있는 경로. 구조도와 분리"),
        ("표준 근거", "KRDS·전자정부 품질관리 지침의 적용 항목"),
        ("검토 메모", "확인 필요 사항과 가정"),
    ]
    for index, (name, desc) in enumerate(sheet_notes, start=start + 1):
        summary.cell(row=index, column=1, value=name).font = section_font
        summary.cell(row=index, column=2, value=desc)
    review_row = start + len(sheet_notes) + 3
    summary.cell(row=review_row, column=1, value="검토 요청").font = section_font
    for index, question in enumerate(REVIEW_QUESTIONS, start=1):
        row = review_row + index
        summary.cell(row=row, column=1, value=f"{index}. {question}")
        summary.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    summary.column_dimensions["A"].width = 26
    summary.column_dimensions["B"].width = 70
    summary.column_dimensions["C"].width = 22
    summary.column_dimensions["D"].width = 22
    summary.freeze_panes = "A4"

    ws = workbook.create_sheet("사이트 구조")
    ws.sheet_properties.tabColor = "2F5597"
    headers = ["No"] + [f"{index}Depth" for index in range(1, depth_count + 1)]
    headers += ["화면 ID", "화면명", "부모 화면", "노출", "URL 패턴", "레이아웃", "접근 역할", "데스크톱", "모바일", "상태", "스크린샷 경로"]
    ws.append(headers)
    widths = [6] + [20] * depth_count + [20, 20, 20, 14, 32, 14, 20, 10, 10, 10, 32]
    style_header(ws, widths, headers)
    for index, page in enumerate(pages, start=1):
        depths = page["menu_path"] + [""] * (depth_count - len(page["menu_path"]))
        append_row(
            ws,
            [index] + depths + [
                page["id"],
                page["title"],
                page["parent_title"] or "",
                page["exposure"],
                page["url"],
                page["layout"],
                ", ".join(page["roles"]),
                bool_label(page["desktop"]),
                bool_label(page["mobile"]),
                page["status"],
                page["screenshot"],
            ],
        )
        row = ws.max_row
        ws.cell(row=row, column=2).font = Font(bold=True)
        ws.cell(row=row, column=2).fill = group_fills[(index - 1) % len(group_fills)]
        status_cell = ws.cell(row=row, column=2 + depth_count + 9)
        status_cell.fill = active_fill if page["status"] == "active" else planned_fill if page["status"] == "planned" else deprecated_fill
    ws.auto_filter.ref = ws.dimensions

    ws = workbook.create_sheet("화면 목록")
    ws.sheet_properties.tabColor = "548235"
    headers = ["화면 ID", "화면명", "메뉴 경로", "URL 패턴", "부모 화면", "레이아웃", "접근 역할", "노출 방식", "데스크톱", "모바일", "상태", "스크린샷 경로", "API 호출", "비고"]
    ws.append(headers)
    style_header(ws, [20, 20, 38, 32, 20, 14, 20, 14, 10, 10, 10, 32, 46, 30], headers)
    for page in pages:
        apis = "\n".join(f"{api['method']} {api['path']}" for api in page["apis"])
        append_row(
            ws,
            [
                page["id"],
                page["title"],
                table_label(page),
                page["url"],
                page["parent_title"],
                page["layout"],
                ", ".join(page["roles"]),
                page["exposure"],
                bool_label(page["desktop"]),
                bool_label(page["mobile"]),
                page["status"],
                page["screenshot"],
                apis,
                page["note"],
            ],
        )
        row = ws.max_row
        ws.cell(row=row, column=11).fill = active_fill if page["status"] == "active" else planned_fill if page["status"] == "planned" else deprecated_fill
    ws.auto_filter.ref = ws.dimensions

    ws = workbook.create_sheet("API 매핑")
    ws.sheet_properties.tabColor = "7F6000"
    headers = ["화면 ID", "화면명", "Method", "API 경로", "호출 시점", "목적", "비고"]
    ws.append(headers)
    style_header(ws, [20, 20, 10, 42, 16, 42, 30], headers)
    for page in pages:
        for api in page["apis"]:
            when = api["when"] or ("on load" if api["method"] == "GET" else "사용자 액션")
            append_row(ws, [page["id"], page["title"], api["method"], api["path"], when, api["purpose"], api["note"]])
    ws.auto_filter.ref = ws.dimensions

    ws = workbook.create_sheet("API only")
    ws.sheet_properties.tabColor = "833C00"
    headers = ["Method", "API 경로", "용도", "호출 주체", "화면 없음 사유", "비고"]
    ws.append(headers)
    style_header(ws, [10, 40, 36, 24, 40, 20], headers)
    for api in api_only:
        append_row(ws, [api["method"], api["path"], api["purpose"], api["caller"], api["reason"], api["note"]])
        for cell in ws[ws.max_row]:
            cell.fill = api_fill
    ws.auto_filter.ref = ws.dimensions

    ws = workbook.create_sheet("표준 근거")
    ws.sheet_properties.tabColor = "7030A0"
    headers = ["구분", "문서", "적용 항목", "내용", "링크"]
    ws.append(headers)
    style_header(ws, [12, 44, 14, 68, 90], headers)
    for standard in standards:
        append_row(ws, [standard["source"], standard["name"], standard["scope"], standard["rule"], standard["url"]])
        link_cell = ws.cell(row=ws.max_row, column=5)
        if standard["url"]:
            link_cell.hyperlink = standard["url"]
            link_cell.font = Font(color="1F5FBF", underline="single")
    ws.auto_filter.ref = ws.dimensions

    ws = workbook.create_sheet("검토 메모")
    ws.sheet_properties.tabColor = "7F7F7F"
    headers = ["No", "구분", "내용", "확인 필요"]
    ws.append(headers)
    style_header(ws, [6, 12, 78, 42], headers)
    for index, warning in enumerate(warnings, start=1):
        append_row(ws, [index, warning["category"], warning["message"], warning["action"]])
    ws.auto_filter.ref = ws.dimensions

    for ws in workbook.worksheets:
        ws.sheet_view.showGridLines = False
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True
    workbook.properties.title = "사이트 구조도"
    workbook.properties.subject = f"Site structure — {meta['site']}"
    workbook.properties.creator = "gorani"
    workbook.save(path)
