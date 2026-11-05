"""Markdown 렌더러. 리포트 모델을 사이트 구조도 Markdown으로 만든다."""

from .constants import REVIEW_QUESTIONS
from .model import bool_label, table_label


def md_cell(value):
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ") or "-"


def build_markdown(model):
    meta = model["meta"]
    pages = model["pages"]
    summary = model["summary"]
    depth_count = summary["depth"]
    warnings = model["warnings"]
    standards = model["standards"]
    api_only = model["api_only"]
    counts = summary["status"]
    headers = ["No"] + [f"{index}Depth" for index in range(1, depth_count + 1)]
    headers += ["화면 ID", "화면명", "부모 화면", "노출", "URL 패턴", "레이아웃", "접근 역할", "데스크톱", "모바일", "상태", "스크린샷 경로"]
    lines = [
        "# 사이트 구조도",
        "",
        f"- 사이트: {meta['site']}",
        f"- 기준 URL: {meta['base_url'] or '-'}",
        f"- 검사 시점: {meta['inspected_at'] or '-'}",
        f"- 수집 기준: {meta['source'] or '-'}",
        f"- 적용 기준: {meta['standard'] or '-'}",
        f"- 검사 역할: {', '.join(meta['roles']) or '-'}",
        f"- 검사 화면 폭: {', '.join(meta['viewports']) or '-'}",
        f"- Depth 규칙: 최소 2Depth, 최대 3Depth (KRDS 메인 메뉴 기준), 현재 {depth_count}Depth",
        f"- 화면: {len(pages)}",
        f"- 활성/계획/폐기: {counts.get('active', 0)} / {counts.get('planned', 0)} / {counts.get('deprecated', 0)}",
        f"- API 매핑: {summary['api_mappings']}",
        f"- API only: {len(api_only)}",
        f"- 검토 메모: {len(warnings)}",
        "",
        "> 이 문서는 실제 프론트 레이아웃을 확인해 정리한 구조도입니다. API 목록은 화면 구조의 근거가 아니며, 화면별 연결과 API only 부록으로만 사용합니다.",
        "",
        "## 사이트 구조",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for index, page in enumerate(pages, start=1):
        depths = page["menu_path"] + [""] * (depth_count - len(page["menu_path"]))
        row = [str(index)] + [md_cell(value or "-") for value in depths]
        row += [
            md_cell(page["id"]),
            md_cell(page["title"]),
            md_cell(page["parent_title"] or "-"),
            md_cell(page["exposure"]),
            md_cell(page["url"] or "-"),
            md_cell(page["layout"] or "-"),
            md_cell(", ".join(page["roles"])),
            bool_label(page["desktop"]),
            bool_label(page["mobile"]),
            md_cell(page["status"]),
            md_cell(page["screenshot"] or "-"),
        ]
        lines.append("| " + " | ".join(row) + " |")
    lines += [
        "",
        "## 화면 목록",
        "",
        "| 화면 ID | 화면명 | 메뉴 경로 | URL 패턴 | 부모 화면 | 레이아웃 | 접근 역할 | 노출 방식 | 데스크톱 | 모바일 | 상태 | 스크린샷 경로 | API 호출 | 비고 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for page in pages:
        apis = "<br>".join(f"{api['method']} {api['path']}" for api in page["apis"]) or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(page["id"]),
                    md_cell(page["title"]),
                    md_cell(table_label(page)),
                    md_cell(page["url"] or "-"),
                    md_cell(page["parent_title"] or "-"),
                    md_cell(page["layout"] or "-"),
                    md_cell(", ".join(page["roles"])),
                    md_cell(page["exposure"]),
                    bool_label(page["desktop"]),
                    bool_label(page["mobile"]),
                    md_cell(page["status"]),
                    md_cell(page["screenshot"] or "-"),
                    md_cell(apis),
                    md_cell(page["note"] or "-"),
                ]
            )
            + " |"
        )
    lines += ["", "## API 매핑", ""]
    if summary["api_mappings"]:
        lines += ["| 화면 ID | 화면명 | Method | API 경로 | 호출 시점 | 목적 |", "| --- | --- | --- | --- | --- | --- |"]
        for page in pages:
            for api in page["apis"]:
                when = api["when"] or ("on load" if api["method"] == "GET" else "사용자 액션")
                lines.append(
                    f"| {md_cell(page['id'])} | {md_cell(page['title'])} | {md_cell(api['method'])} | {md_cell(api['path'])} | {md_cell(when)} | {md_cell(api['purpose'] or '-')} |"
                )
    else:
        lines.append("- API 매핑 없음")
    lines += ["", "## API only", ""]
    if api_only:
        lines += ["| Method | API 경로 | 용도 | 호출 주체 | 화면 없음 사유 |", "| --- | --- | --- | --- | --- |"]
        for api in api_only:
            lines.append(
                f"| {md_cell(api['method'])} | {md_cell(api['path'])} | {md_cell(api['purpose'] or '-')} | {md_cell(api['caller'] or '-')} | {md_cell(api['reason'] or '-')} |"
            )
    else:
        lines.append("- API only 없음")
    lines += ["", "## 표준 근거", ""]
    if standards:
        lines += ["| 구분 | 문서 | 적용 항목 | 내용 | 링크 |", "| --- | --- | --- | --- | --- |"]
        for standard in standards:
            link = f"[{md_cell(standard['name'])}]({standard['url']})" if standard["url"] else md_cell(standard["name"])
            lines.append(
                f"| {md_cell(standard['source'] or '-')} | {link} | {md_cell(standard['scope'] or '-')} | {md_cell(standard['rule'] or '-')} | {md_cell(standard['url'] or '-')} |"
            )
    else:
        lines.append("- 표준 근거 없음")
    lines += ["", "## 검토 메모", ""]
    if warnings:
        lines += ["| No | 구분 | 내용 | 확인 필요 |", "| --- | --- | --- | --- |"]
        for index, warning in enumerate(warnings, start=1):
            lines.append(
                f"| {index} | {md_cell(warning['category'])} | {md_cell(warning['message'])} | {md_cell(warning['action'] or '-')} |"
            )
    else:
        lines.append("- 검토 메모 없음")
    lines += ["", "## 검토 요청", ""]
    for index, question in enumerate(REVIEW_QUESTIONS, start=1):
        lines.append(f"{index}. {question}")
    return "\n".join(lines).rstrip() + "\n"
