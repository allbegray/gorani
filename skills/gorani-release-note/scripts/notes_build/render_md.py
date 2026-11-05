"""릴리스 노트를 Markdown으로 렌더링한다."""

from .constants import LABELS
from .model import safe_href, text


def item_lines(item, labels, default_label=None):
    lines = []
    description = text(item.get("description"))
    if description:
        lines.append(description)
    action = text(item.get("action"))
    href = safe_href(item.get("link"))
    if (action or href) and lines:
        lines.append("")
    if action:
        label = text(item.get("action_label")) or default_label or labels["how_to_use"]
        lines.append(f"- {label}: {action}")
    if href:
        lines.append(f"- [{labels['learn_more']}](<{href}>)")
    return lines


def render_markdown(model, labels=None):
    data = model.get("content", model)
    if labels is None:
        labels = LABELS[model["meta"]["language"]]
    product = text(data.get("product"))
    version = text(data.get("version"))
    release_date = text(data.get("release_date"))
    lines = [f"# {product} {version} {labels['release_notes']}".strip(), ""]
    meta = [release_date]
    if text(data.get("audience")):
        meta.append(f"{labels['audience']}: {text(data.get('audience'))}")
    lines.extend([" · ".join(part for part in meta if part), ""])

    headline = text(data.get("headline"))
    summary = text(data.get("summary"))
    if headline:
        lines.extend([f"**{headline}**", ""])
    if summary:
        lines.extend([summary, ""])

    breaking = data.get("breaking_changes") or []
    if breaking:
        lines.extend([f"## {labels['breaking']}", ""])
        for item in breaking:
            lines.extend([f"### {text(item.get('title'))}", ""])
            lines.extend(item_lines(item, labels, labels["action"]))
            lines.append("")

    highlights = data.get("highlights") or []
    if highlights:
        lines.extend([f"## {labels['highlights']}", ""])
        for item in highlights:
            title = text(item.get("title"))
            description = text(item.get("description"))
            line = f"- **{title}**"
            if description:
                line += f" — {description}"
            href = safe_href(item.get("link"))
            if href:
                line += f" ([{labels['learn_more']}](<{href}>))"
            lines.append(line)
        lines.append("")

    for section in data.get("sections") or []:
        name = text(section.get("name"))
        items = section.get("items") or []
        if not name or not items:
            continue
        lines.extend([f"## {name}", ""])
        for item in items:
            lines.extend([f"### {text(item.get('title'))}", ""])
            lines.extend(item_lines(item, labels))
            lines.append("")

    upgrade_notes = data.get("upgrade_notes") or []
    if upgrade_notes:
        lines.extend([f"## {labels['upgrade_notes']}", ""])
        for note in upgrade_notes:
            lines.append(f"- {text(note)}")
        lines.append("")

    known_issues = data.get("known_issues") or []
    if known_issues:
        lines.extend([f"## {labels['known_issues']}", ""])
        for issue in known_issues:
            lines.append(f"- {text(issue)}")
        lines.append("")

    support = data.get("support") or {}
    support_url = safe_href(support.get("url"))
    support_email = text(support.get("email"))
    if support_url or support_email:
        lines.extend([f"## {labels['support']}", ""])
        if support_url:
            lines.append(f"- <{support_url}>")
        if support_email:
            lines.append(f"- {support_email}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
