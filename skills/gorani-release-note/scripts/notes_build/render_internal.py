"""내부 검토용 commit 매핑·경고·확인 목록을 Markdown으로 렌더링한다."""

from .model import limit_value, text


def markdown_cell(value):
    return text(value).replace("|", "\\|").replace("\n", " ")


def render_internal(model, warnings=None, strict_issues=None, limits=None, auto_notes=None):
    data = model.get("content", model)
    if warnings is None:
        warnings = model.get("warnings", [])
    if strict_issues is None:
        strict_issues = model.get("strict_issues", [])
    if limits is None:
        limits = model.get("limits") or {
            "short": limit_value(data, "short"),
            "store": limit_value(data, "store"),
        }
    if auto_notes is None:
        auto_notes = model.get("auto_notes", [])
    commits = model.get("commits") or data.get("commits") or []
    summary = model.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    included = summary.get(
        "included", sum(1 for commit in commits if commit.get("included", True))
    )
    excluded = summary.get("excluded", len(commits) - included)
    item_count = summary.get(
        "items",
        sum(len(section.get("items") or []) for section in data.get("sections") or []),
    )
    lines = [
        "# 릴리스 노트 검토 기록",
        "",
        "이 파일은 내부 검토용입니다. 고객에게 배포하지 않습니다.",
        "",
        f"- 제품: {text(data.get('product'))}",
        f"- 버전: {text(data.get('version'))}",
        f"- 배포일: {text(data.get('release_date'))}",
        f"- 대상: {text(data.get('audience'))}",
        f"- 언어: {text(data.get('language')) or 'ko'}",
        f"- commit: {len(commits)} (포함 {included}, 제외 {excluded})",
        f"- 섹션 항목: {item_count}",
        f"- 글자 수 제한: short {limits['short']}, store {limits['store']}",
        "",
    ]
    range_info = data.get("range") or model.get("meta", {}).get("range") or {}
    if range_info:
        lines.extend(
            [
                f"- 비교 범위: {text(range_info.get('from'))}..{text(range_info.get('to'))}",
                "",
            ]
        )
    if auto_notes:
        lines.extend(["## 자동 생성", ""])
        for note in auto_notes:
            lines.append(f"- {note}")
        lines.append("")
    if warnings:
        lines.extend(["## 경고", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    if strict_issues:
        lines.extend(["## Strict에서 오류로 처리될 항목", ""])
        for issue in strict_issues:
            lines.append(f"- {issue}")
        lines.append("")

    lines.extend(
        [
            "## Commit 매핑",
            "",
            "| Hash | 날짜 | 제목 | 분류 | 포함 | 비고 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for commit in commits:
        note = commit.get("note") if commit.get("included", True) else commit.get("reason")
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_cell(commit.get("short_hash") or commit.get("hash")),
                    markdown_cell(commit.get("date")),
                    markdown_cell(commit.get("subject")),
                    markdown_cell(commit.get("suggested_category")),
                    "예" if commit.get("included", True) else "아니오",
                    markdown_cell(note),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 배포 전 확인",
            "",
            "- 고객 문장의 모든 주장이 commit 또는 diff로 확인됐는가",
            "- commit hash, 이슈 번호, 직원 이름, 내부 URL이 고객 문구에 없는가",
            "- 업그레이드 전 확인 항목에 구체적인 조치가 있는가",
            "- 링크가 https 또는 mailto이고 실제로 열리는가",
            "- short/store 요약이 글자 수 제한 안에 있는가",
            "- 지원 경로가 고객에게 보이는가",
            "",
        ]
    )
    return "\n".join(lines)
