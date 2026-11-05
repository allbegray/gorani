"""입력 JSON을 Markdown·HTML·텍스트 렌더러가 소비하는 리포트 모델로 만든다."""

import re

from .constants import DEFAULT_LIMITS, GENERATOR, OUTPUT_FORMATS, SCHEMA_VERSION


def text(value):
    return str(value or "").strip()


def safe_href(value):
    value = text(value)
    if re.match(r"^(https?://|mailto:)", value, re.I):
        return value
    return ""


def limit_value(data, key):
    limits = data.get("limits") or {}
    try:
        value = int(limits.get(key, DEFAULT_LIMITS[key]))
    except (TypeError, ValueError):
        return DEFAULT_LIMITS[key]
    return value if value > 0 else DEFAULT_LIMITS[key]


def truncate(value, limit):
    if len(value) <= limit:
        return value, False
    cut = value[:limit]
    last_break = -1
    for match in re.finditer(r"\n|[.!?。！？]\s", cut):
        last_break = match.end()
    if last_break >= limit * 0.5:
        result = cut[:last_break].rstrip()
    else:
        result = cut.rstrip()
    if result and result[-1] not in ".!?。！？":
        if len(result) < limit:
            result += "…"
    return result[:limit], True


def auto_short_summary(data, labels, limit):
    product = text(data.get("product"))
    version = text(data.get("version"))
    parts = [f"{product} {version} {labels['update']}".strip()]
    highlights = data.get("highlights") or []
    for item in highlights[:2]:
        title = text(item.get("title"))
        description = text(item.get("description"))
        if title or description:
            parts.append(f"• {title}: {description}".strip())
    if len(parts) == 1:
        for section in (data.get("sections") or [])[:2]:
            for item in (section.get("items") or [])[:2]:
                title = text(item.get("title"))
                description = text(item.get("description"))
                if title or description:
                    parts.append(f"• {title}: {description}".strip())
    for breaking in (data.get("breaking_changes") or [])[:1]:
        title = text(breaking.get("title"))
        if title:
            parts.append(f"• {labels['breaking']}: {title}")
    parts.append(labels["see_app"])
    return truncate("\n".join(parts), limit)


def auto_store_summary(data, labels, limit):
    parts = []
    title = f"{text(data.get('product'))} {text(data.get('version'))}".strip()
    if title:
        parts.append(title)
    headline = text(data.get("headline"))
    summary = text(data.get("summary"))
    if headline:
        parts.append(headline)
    if summary:
        parts.append(summary)
    for breaking in data.get("breaking_changes") or []:
        title = text(breaking.get("title"))
        action = text(breaking.get("action"))
        if title:
            parts.append(f"[{labels['breaking']}] {title}")
            if action:
                action_label = text(breaking.get("action_label")) or labels["action"]
                parts.append(f"- {action_label}: {action}")
    for section in data.get("sections") or []:
        items = section.get("items") or []
        if not items:
            continue
        parts.append(f"[{text(section.get('name'))}]")
        for item in items:
            title = text(item.get("title"))
            description = text(item.get("description"))
            action = text(item.get("action"))
            line = f"- {title}: {description}".strip()
            if action:
                action_label = text(item.get("action_label")) or labels["how_to_use"]
                line += f" ({action_label}: {action})"
            parts.append(line)
    support = data.get("support") or {}
    support_url = safe_href(support.get("url"))
    upgrade_notes = data.get("upgrade_notes") or []
    if upgrade_notes:
        parts.append(f"[{labels['upgrade_notes']}]")
        for note in upgrade_notes:
            parts.append(f"- {text(note)}")
    known_issues = data.get("known_issues") or []
    if known_issues:
        parts.append(f"[{labels['known_issues']}]")
        for issue in known_issues:
            parts.append(f"- {text(issue)}")
    if support_url:
        parts.append(f"{labels['details']}: {support_url}")
    return truncate("\n".join(parts), limit)


def build_internal_mappings(commits):
    mappings = []
    for commit in commits:
        included = commit.get("included", True)
        note = commit.get("note") if included else commit.get("reason")
        mappings.append(
            {
                "hash": text(commit.get("hash")),
                "short_hash": text(commit.get("short_hash")),
                "date": text(commit.get("date")),
                "subject": text(commit.get("subject")),
                "category": text(commit.get("suggested_category")),
                "section": text(commit.get("suggested_section")),
                "breaking": bool(commit.get("breaking", False)),
                "included": bool(included),
                "note": text(note),
            }
        )
    return mappings


def build_report_model(
    data,
    input_path,
    formats,
    labels,
    language,
    limits,
    warnings,
    strict_issues,
    errors,
    generated_at,
):
    auto_notes = []
    short_text = ""
    store_text = ""
    if "short" in formats:
        short_summary = text(data.get("short_summary"))
        if short_summary:
            short_text = short_summary
        else:
            short_text, truncated = auto_short_summary(data, labels, limits["short"])
            auto_notes.append(
                "short_summary 가 없어 highlights/sections 에서 자동 생성했습니다."
            )
            if truncated:
                warnings.append(f"short 요약을 {limits['short']}자로 줄였습니다.")
    if "store" in formats:
        store_summary = text(data.get("store_summary"))
        if store_summary:
            store_text = store_summary
        else:
            store_text, truncated = auto_store_summary(data, labels, limits["store"])
            auto_notes.append(
                "store_summary 가 없어 sections 에서 자동 생성했습니다."
            )
            if truncated:
                warnings.append(f"store 요약을 {limits['store']}자로 줄였습니다.")

    sections = data.get("sections") or []
    highlights = data.get("highlights") or []
    commits = data.get("commits") or []
    included = sum(1 for commit in commits if commit.get("included", True))
    excluded = len(commits) - included
    item_count = sum(len(section.get("items") or []) for section in sections)

    content = {
        "product": text(data.get("product")),
        "version": text(data.get("version")),
        "release_date": text(data.get("release_date")),
        "language": text(data.get("language")),
        "audience": text(data.get("audience")),
        "headline": text(data.get("headline")),
        "summary": text(data.get("summary")),
        "highlights": highlights,
        "sections": sections,
        "breaking_changes": data.get("breaking_changes") or [],
        "known_issues": data.get("known_issues") or [],
        "upgrade_notes": data.get("upgrade_notes") or [],
        "support": data.get("support") or {},
        "short_summary": text(data.get("short_summary")),
        "store_summary": text(data.get("store_summary")),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "generator": GENERATOR,
            "generated_at": generated_at,
            "input": str(input_path),
            "product": content["product"],
            "version": content["version"],
            "release_date": content["release_date"],
            "language": language,
            "audience": content["audience"],
            "formats": [item for item in OUTPUT_FORMATS if item in formats],
            "range": data.get("range") or {},
        },
        "summary": {
            "sections": len(sections),
            "highlights": len(highlights),
            "items": item_count,
            "commits": len(commits),
            "included": included,
            "excluded": excluded,
            "short_chars": len(short_text) if "short" in formats else 0,
            "short_limit": limits["short"],
            "store_chars": len(store_text) if "store" in formats else 0,
            "store_limit": limits["store"],
            "auto_summary": bool(auto_notes),
        },
        "content": content,
        "summaries": {"short": short_text, "store": store_text},
        "limits": limits,
        "warnings": warnings,
        "strict_issues": strict_issues,
        "auto_notes": auto_notes,
        "errors": errors,
        "commits": commits,
        "internal": {
            "mappings": build_internal_mappings(commits),
            "included": included,
            "excluded": excluded,
        },
        "logs": data.get("logs") or [],
    }
