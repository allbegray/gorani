"""XLSX 고지 보고서 렌더러. openpyxl은 이 모듈에서만 사용한다."""

import sys
from collections import Counter

from .constants import EXCEL_TEXT_LIMIT, STATUS_LABELS


def write_workbook(path, model, name):
    meta = model["meta"]
    packages = model["packages"]
    review = model["review"]
    groups = model["groups"]
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        sys.exit(
            "엑셀을 만들려면 openpyxl 이 필요합니다. "
            "'python3 -m pip install --user openpyxl' 실행 후 다시 시도하세요. "
            "HTML 과 md 는 openpyxl 없이도 생성됩니다."
        )

    header_fill = PatternFill("solid", fgColor="1F3864")
    header_font = Font(color="FFFFFF", bold=True)
    title_font = Font(size=14, bold=True)
    section_font = Font(bold=True)
    thin = Side(style="thin", color="BFBFBF")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    status_fills = {
        "none": PatternFill("solid", fgColor="D9D9D9"),
        "notice": PatternFill("solid", fgColor="C6E0B4"),
        "weak": PatternFill("solid", fgColor="FFE699"),
        "strong": PatternFill("solid", fgColor="F4B183"),
        "network": PatternFill("solid", fgColor="F8CBAD"),
        "unknown": PatternFill("solid", fgColor="E4DFEC"),
    }

    def style_header(ws, widths):
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        for index, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(index)].width = width
        ws.freeze_panes = "A2"

    def write_summary(ws):
        ws["A1"] = "오픈소스 라이선스 고지"
        ws["A1"].font = title_font
        ws.merge_cells("A1:D1")
        scope_counts = Counter(p["scope"] for p in packages)
        status_counts = Counter(p["status"] for p in packages)
        rows = [
            ("프로젝트", meta.get("project", "")),
            ("앱 버전", meta.get("app_version", "")),
            ("생성 시각", meta.get("generated_at", "")),
            ("대상 패키지", len(packages)),
            ("런타임", scope_counts.get("runtime", 0)),
            ("개발", scope_counts.get("dev", 0)),
            ("확인 필요(범위)", scope_counts.get("unknown", 0)),
            ("검토 필요 항목", len(review)),
            ("라이선스 전문 없음", sum(1 for p in packages if not p["license_text"])),
        ]
        for index, (label, value) in enumerate(rows, start=3):
            ws.cell(row=index, column=1, value=label).font = section_font
            ws.cell(row=index, column=2, value=value)
        start = len(rows) + 5
        ws.cell(row=start, column=1, value="고지 의무 집계").font = section_font
        for offset, status in enumerate(STATUS_LABELS, start=1):
            row = start + offset
            cell = ws.cell(row=row, column=1, value=STATUS_LABELS[status])
            cell.fill = status_fills[status]
            cell.border = border
            ws.cell(row=row, column=2, value=status_counts.get(status, 0)).border = border
        note_row = start + len(STATUS_LABELS) + 3
        ws.cell(row=note_row, column=1, value="생성 규칙").font = section_font
        ws.cell(
            row=note_row + 1,
            column=1,
            value=f"라이선스 전문은 {name}.html 과 {name}.md 에 원문 그대로 수록",
        )
        ws.cell(row=note_row + 2, column=1, value="copyleft 와 라이선스 미확인 항목은 검토 필요 시트에서 확인")
        ws.column_dimensions["A"].width = 30
        ws.column_dimensions["B"].width = 48

    def write_packages(ws):
        headers = [
            "패키지",
            "버전",
            "라이선스",
            "고지 의무",
            "저작권 표시",
            "범위",
            "의존성",
            "전문",
            "라이선스 파일",
            "저장소",
        ]
        ws.append(headers)
        style_header(ws, [26, 12, 22, 18, 46, 10, 10, 8, 48, 44])
        for package in packages:
            ws.append(
                [
                    package["name"],
                    package["version"],
                    package["license"] or "unknown",
                    STATUS_LABELS[package["status"]],
                    package["copyright"],
                    package["scope"],
                    package["dependency"],
                    "있음" if package["license_text"] else "없음",
                    package["license_source"],
                    package["repository"],
                ]
            )
            row = ws.max_row
            for cell in ws[row]:
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)
            ws.cell(row=row, column=4).fill = status_fills[package["status"]]
            if not package["license_text"]:
                ws.cell(row=row, column=8).fill = PatternFill("solid", fgColor="F8CBAD")

    def write_license_texts(ws):
        headers = ["라이선스", "패키지 수", "글자 수", "전문", "비고"]
        ws.append(headers)
        style_header(ws, [24, 10, 10, 110, 40])
        for group in groups:
            for variant in group["variants"]:
                text = variant["text"]
                truncated = len(text) > EXCEL_TEXT_LIMIT
                shown = text[:EXCEL_TEXT_LIMIT]
                note = "전문 생략, html 파일 참조" if truncated else ""
                ws.append(
                    [group["license"], len(variant["packages"]), len(text), shown, note]
                )
                row = ws.max_row
                for cell in ws[row]:
                    cell.border = border
                    cell.alignment = Alignment(vertical="top", wrap_text=True)

    def write_review(ws):
        headers = ["패키지", "버전", "라이선스", "사유", "조치"]
        ws.append(headers)
        style_header(ws, [26, 12, 22, 52, 52])
        for item in review:
            package = item["package"]
            ws.append(
                [
                    package["name"],
                    package["version"],
                    package["license"] or "unknown",
                    item["reason"],
                    item["action"],
                ]
            )
            row = ws.max_row
            for cell in ws[row]:
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

    def write_logs(ws):
        headers = ["도구", "명령", "상태", "비고"]
        ws.append(headers)
        style_header(ws, [22, 90, 12, 40])
        for log in model.get("logs", []):
            ws.append(
                [
                    log.get("tool", ""),
                    log.get("command", ""),
                    log.get("status", ""),
                    log.get("note", ""),
                ]
            )
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=4):
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(vertical="top", wrap_text=True)

    workbook = Workbook()
    summary = workbook.active
    summary.title = "요약"
    write_summary(summary)
    write_packages(workbook.create_sheet("패키지"))
    write_license_texts(workbook.create_sheet("라이선스 전문"))
    write_review(workbook.create_sheet("검토 필요"))
    write_logs(workbook.create_sheet("실행 로그"))
    workbook.save(path)
