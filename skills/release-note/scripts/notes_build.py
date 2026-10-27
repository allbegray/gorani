#!/usr/bin/env python3
"""고객용 릴리스 노트를 만든다.

입력: 큐레이션된 릴리스 노트 JSON (SKILL.md 의 입력 형식 참고)
출력: release-notes.md, release-notes.html, release-notes-short.txt,
      release-notes-store.txt, release-notes-internal.md
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

LABELS = {
    "ko": {
        "release_notes": "릴리스 노트",
        "date": "배포일",
        "audience": "대상",
        "highlights": "한눈에 보기",
        "breaking": "업그레이드 전 확인",
        "known_issues": "알려진 문제",
        "upgrade_notes": "업그레이드 참고",
        "support": "도움이 필요하신가요?",
        "how_to_use": "사용 방법",
        "action": "조치",
        "learn_more": "자세히 보기",
        "update": "업데이트",
        "see_app": "자세한 내용은 앱에서 확인해 주세요.",
        "details": "자세한 내용",
    },
    "en": {
        "release_notes": "Release notes",
        "date": "Released",
        "audience": "Audience",
        "highlights": "Highlights",
        "breaking": "Before you upgrade",
        "known_issues": "Known issues",
        "upgrade_notes": "Upgrade notes",
        "support": "Need help?",
        "how_to_use": "How to use",
        "action": "Action",
        "learn_more": "Learn more",
        "update": "update",
        "see_app": "See the app for details.",
        "details": "Details",
    },
}

DEFAULT_LIMITS = {"short": 500, "store": 4000}


def parse_args():
    parser = argparse.ArgumentParser(description="고객용 릴리스 노트 생성")
    parser.add_argument("--input", required=True, help="큐레이션된 릴리스 노트 JSON")
    parser.add_argument("--outdir", default="docs/releases", help="출력 디렉터리")
    parser.add_argument("--name", default="release-notes", help="출력 파일 기본 이름")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="commit 매핑 누락, 지원 경로 누락, 잘못된 링크를 오류로 처리",
    )
    return parser.parse_args()


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


def render_markdown(data, labels):
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


def render_html(data, labels):
    product = text(data.get("product"))
    version = text(data.get("version"))
    release_date = text(data.get("release_date"))
    audience = text(data.get("audience"))
    headline = text(data.get("headline"))
    summary = text(data.get("summary"))
    language = text(data.get("language")) or "ko"
    lang = language if language in ("ko", "en") else "en"
    document_title = f"{product} {version} — {labels['release_notes']}".strip()

    css = """
:root {
  color-scheme: light dark;
  --bg: #fbfaf7;
  --fg: #1d1b18;
  --muted: #6b655d;
  --line: #e5e0d8;
  --panel: #ffffff;
  --accent: #8a4b1f;
  --accent-soft: #f6e7da;
  --warn: #7a4a00;
  --warn-bg: #fff4dd;
  --warn-line: #e8c27a;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #141210;
    --fg: #eee9e1;
    --muted: #a9a198;
    --line: #302b26;
    --panel: #1b1815;
    --accent: #e6b184;
    --accent-soft: #3a2a1d;
    --warn: #ffd28a;
    --warn-bg: #2d2415;
    --warn-line: #6b5226;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font: 16px/1.65 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Hiragino Sans", "Noto Sans KR", sans-serif;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
main, header, footer { max-width: 46rem; margin: 0 auto; padding: 0 1.25rem; }
header { padding-top: 3rem; padding-bottom: 1.5rem; }
.eyebrow { margin: 0; color: var(--accent); font-size: .75rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
h1 { margin: .5rem 0; font-size: 2rem; line-height: 1.2; letter-spacing: -.02em; }
.meta { margin: 0; color: var(--muted); font-size: .875rem; }
.headline { margin: 1.5rem 0 .5rem; font-size: 1.125rem; font-weight: 700; }
.summary { margin: 0; color: var(--muted); }
main { padding-bottom: 3rem; }
section { padding: 1.75rem 0; border-top: 1px solid var(--line); }
h2 { margin: 0 0 1rem; font-size: 1.25rem; }
h3 { margin: 1.25rem 0 .35rem; font-size: 1rem; }
p { margin: .4rem 0; }
ul { margin: .4rem 0; padding-left: 1.2rem; }
li { margin: .3rem 0; }
.callout { margin: 1.5rem 0 0; padding: 1rem 1.1rem; background: var(--warn-bg); border: 1px solid var(--warn-line); border-radius: .75rem; }
.callout h2 { color: var(--warn); }
.callout h3 { color: var(--warn); }
.highlights { display: grid; gap: .75rem; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); }
.card { padding: .9rem 1rem; background: var(--panel); border: 1px solid var(--line); border-radius: .75rem; }
.card h3 { margin: 0 0 .3rem; }
.card p { color: var(--muted); font-size: .9375rem; }
.action { margin-top: .4rem; color: var(--muted); font-size: .875rem; }
a { color: var(--accent); text-underline-offset: 2px; }
footer { padding-top: 1.5rem; padding-bottom: 3rem; color: var(--muted); font-size: .8125rem; border-top: 1px solid var(--line); }
@media print {
  body { background: #fff; color: #000; font-size: 11pt; }
  section { break-inside: avoid-page; }
  a { color: #000; }
}
""".strip()

    parts = [
        "<!doctype html>",
        f'<html lang="{lang}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'\">",
        f"<title>{html.escape(document_title)}</title>",
        f"<style>\n{css}\n</style>",
        "</head>",
        "<body>",
        "<header>",
        f'<p class="eyebrow">{html.escape(labels["release_notes"])}</p>',
        f"<h1>{html.escape(product)} {html.escape(version)}</h1>",
        f'<p class="meta">{html.escape(release_date)}'
        + (f" · {html.escape(audience)}" if audience else "")
        + "</p>",
    ]
    if headline:
        parts.append(f'<p class="headline">{html.escape(headline)}</p>')
    if summary:
        parts.append(f'<p class="summary">{html.escape(summary)}</p>')
    parts.append("</header>")
    parts.append("<main>")

    breaking = data.get("breaking_changes") or []
    if breaking:
        parts.append('<section class="callout">')
        parts.append(f"<h2>{html.escape(labels['breaking'])}</h2>")
        for item in breaking:
            parts.append(f"<h3>{html.escape(text(item.get('title')))}</h3>")
            description = text(item.get("description"))
            if description:
                parts.append(f"<p>{html.escape(description)}</p>")
            action = text(item.get("action"))
            if action:
                action_label = text(item.get("action_label")) or labels["action"]
                parts.append(
                    f'<p class="action">{html.escape(action_label)}: '
                    f"{html.escape(action)}</p>"
                )
            href = safe_href(item.get("link"))
            if href:
                parts.append(
                    f'<p><a href="{html.escape(href, quote=True)}" '
                    f'rel="noopener noreferrer">{html.escape(labels["learn_more"])}</a></p>'
                )
        parts.append("</section>")

    highlights = data.get("highlights") or []
    if highlights:
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(labels['highlights'])}</h2>")
        parts.append('<div class="highlights">')
        for item in highlights:
            parts.append('<div class="card">')
            parts.append(f"<h3>{html.escape(text(item.get('title')))}</h3>")
            description = text(item.get("description"))
            if description:
                parts.append(f"<p>{html.escape(description)}</p>")
            href = safe_href(item.get("link"))
            if href:
                parts.append(
                    f'<p><a href="{html.escape(href, quote=True)}" '
                    f'rel="noopener noreferrer">{html.escape(labels["learn_more"])}</a></p>'
                )
            parts.append("</div>")
        parts.append("</div>")
        parts.append("</section>")

    for section in data.get("sections") or []:
        name = text(section.get("name"))
        items = section.get("items") or []
        if not name or not items:
            continue
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(name)}</h2>")
        for item in items:
            parts.append(f"<h3>{html.escape(text(item.get('title')))}</h3>")
            description = text(item.get("description"))
            if description:
                parts.append(f"<p>{html.escape(description)}</p>")
            action = text(item.get("action"))
            if action:
                action_label = text(item.get("action_label")) or labels["how_to_use"]
                parts.append(
                    f'<p class="action">{html.escape(action_label)}: '
                    f"{html.escape(action)}</p>"
                )
            href = safe_href(item.get("link"))
            if href:
                parts.append(
                    f'<p><a href="{html.escape(href, quote=True)}" '
                    f'rel="noopener noreferrer">{html.escape(labels["learn_more"])}</a></p>'
                )
        parts.append("</section>")

    upgrade_notes = data.get("upgrade_notes") or []
    if upgrade_notes:
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(labels['upgrade_notes'])}</h2>")
        parts.append("<ul>")
        for note in upgrade_notes:
            parts.append(f"<li>{html.escape(text(note))}</li>")
        parts.append("</ul>")
        parts.append("</section>")

    known_issues = data.get("known_issues") or []
    if known_issues:
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(labels['known_issues'])}</h2>")
        parts.append("<ul>")
        for issue in known_issues:
            parts.append(f"<li>{html.escape(text(issue))}</li>")
        parts.append("</ul>")
        parts.append("</section>")

    support = data.get("support") or {}
    support_url = safe_href(support.get("url"))
    support_email = text(support.get("email"))
    if support_url or support_email:
        parts.append("<section>")
        parts.append(f"<h2>{html.escape(labels['support'])}</h2>")
        parts.append("<ul>")
        if support_url:
            parts.append(
                f'<li><a href="{html.escape(support_url, quote=True)}" '
                f'rel="noopener noreferrer">{html.escape(support_url)}</a></li>'
            )
        if support_email:
            parts.append(
                f'<li><a href="mailto:{html.escape(support_email, quote=True)}">'
                f"{html.escape(support_email)}</a></li>"
            )
        parts.append("</ul>")
        parts.append("</section>")

    parts.extend(["</main>", "<footer>", f"{html.escape(product)} {html.escape(version)}", "</footer>"])
    parts.extend(["</body>", "</html>"])
    return "\n".join(parts) + "\n"


def validate(data):
    errors = []
    warnings = []
    strict_issues = []
    for key, label in (("product", "제품명"), ("version", "버전"), ("release_date", "배포일")):
        if not text(data.get(key)):
            errors.append(f"{label}이(가) 비어 있습니다.")

    highlights = data.get("highlights") or []
    if not isinstance(highlights, list):
        errors.append("highlights는 배열이어야 합니다.")
        highlights = []
    sections = data.get("sections") or []
    if not isinstance(sections, list):
        errors.append("sections는 배열이어야 합니다.")
        sections = []
    item_count = 0
    for index, item in enumerate(highlights, start=1):
        if not isinstance(item, dict):
            errors.append(f"highlights {index}가 객체가 아닙니다.")
            continue
        if not text(item.get("title")):
            errors.append(f"highlights {index}의 title이 비어 있습니다.")
    seen_sections = set()
    for section in sections:
        if not isinstance(section, dict):
            errors.append("sections 항목이 객체가 아닙니다.")
            continue
        name = text(section.get("name"))
        if not name:
            errors.append("sections 항목의 name이 비어 있습니다.")
            continue
        if name in seen_sections:
            strict_issues.append(f"섹션 이름이 중복됩니다: {name}")
        seen_sections.add(name)
        items = section.get("items") or []
        if not isinstance(items, list):
            errors.append(f"'{name}' 섹션의 items가 배열이 아닙니다.")
            continue
        if not items:
            strict_issues.append(f"섹션에 항목이 없습니다: {name}")
        for item in items:
            if not isinstance(item, dict):
                errors.append(f"'{name}' 섹션에 객체가 아닌 항목이 있습니다.")
                continue
            item_count += 1
            if not text(item.get("title")):
                errors.append(f"{name} 섹션에 title이 없는 항목이 있습니다.")
            if not text(item.get("description")):
                errors.append(
                    f"{name} / {text(item.get('title'))} 항목의 description이 비어 있습니다."
                )
            link = text(item.get("link"))
            if link and not safe_href(link):
                strict_issues.append(
                    f"허용되지 않는 링크입니다(https/mailto만 허용): {link}"
                )
    if not highlights and item_count == 0:
        errors.append("highlights 또는 sections items가 하나 이상 필요합니다.")

    breaking = data.get("breaking_changes") or []
    if not isinstance(breaking, list):
        errors.append("breaking_changes는 배열이어야 합니다.")
        breaking = []
    for item in breaking:
        if not isinstance(item, dict):
            errors.append("breaking_changes 항목이 객체가 아닙니다.")
            continue
        if not text(item.get("action")):
            errors.append(
                f"업그레이드 항목 '{text(item.get('title'))}'에 action이 없습니다."
            )
        link = text(item.get("link"))
        if link and not safe_href(link):
            strict_issues.append(
                f"업그레이드 항목에 허용되지 않는 링크가 있습니다: {link}"
            )

    for key, label in (("known_issues", "알려진 문제"), ("upgrade_notes", "업그레이드 참고")):
        value = data.get(key) or []
        if not isinstance(value, list):
            errors.append(f"{label}는 배열이어야 합니다.")
            continue
        for note in value:
            if not text(note):
                warnings.append(f"{label}에 빈 항목이 있습니다.")

    support = data.get("support") or {}
    if not isinstance(support, dict):
        errors.append("support는 객체여야 합니다.")
        support = {}
    support_url = text(support.get("url"))
    support_email = text(support.get("email"))
    if support_url and not safe_href(support_url):
        strict_issues.append(f"지원 URL이 허용되지 않는 형식입니다: {support_url}")
    if support_email and "@" not in support_email:
        strict_issues.append(f"지원 이메일 형식이 아닙니다: {support_email}")
    if not support_url and not support_email:
        strict_issues.append("고객이 문의할 지원 URL 또는 이메일이 없습니다.")

    limits = {
        "short": limit_value(data, "short"),
        "store": limit_value(data, "store"),
    }
    short_summary = text(data.get("short_summary"))
    store_summary = text(data.get("store_summary"))
    if short_summary and len(short_summary) > limits["short"]:
        errors.append(
            f"short_summary가 {len(short_summary)}자입니다. 제한 {limits['short']}자를 넘습니다."
        )
    if store_summary and len(store_summary) > limits["store"]:
        errors.append(
            f"store_summary가 {len(store_summary)}자입니다. 제한 {limits['store']}자를 넘습니다."
        )

    commits = data.get("commits") or []
    if not isinstance(commits, list):
        errors.append("commits는 배열이어야 합니다.")
        commits = []
    if not commits:
        strict_issues.append("commit 매핑이 없습니다.")
    for commit in commits:
        if not isinstance(commit, dict):
            strict_issues.append("commit 항목이 객체가 아닙니다.")
            continue
        subject = text(commit.get("subject")) or text(commit.get("short_hash"))
        if commit.get("included", True):
            if not text(commit.get("note")):
                strict_issues.append(f"포함 commit에 note가 없습니다: {subject}")
        elif not text(commit.get("reason")):
            strict_issues.append(f"제외 commit에 reason이 없습니다: {subject}")

    raw_warnings = data.get("warnings") or []
    if not isinstance(raw_warnings, list):
        warnings.append("warnings는 배열이어야 합니다. 무시했습니다.")
    else:
        for warning in raw_warnings:
            warnings.append(text(warning))
    return errors, warnings, strict_issues, limits


def markdown_cell(value):
    return text(value).replace("|", "\\|").replace("\n", " ")


def render_internal(data, warnings, strict_issues, limits, auto_notes):
    commits = data.get("commits") or []
    included = sum(1 for commit in commits if commit.get("included", True))
    excluded = len(commits) - included
    item_count = sum(len(section.get("items") or []) for section in data.get("sections") or [])
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
    range_info = data.get("range") or {}
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


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_file():
        sys.exit(f"입력 파일이 없습니다: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"입력 JSON 을 읽지 못했습니다: {error}")
    if not isinstance(data, dict):
        sys.exit("입력 JSON 의 최상위가 객체가 아닙니다.")

    errors, warnings, strict_issues, limits = validate(data)
    if errors:
        print(json.dumps({"errors": errors, "warnings": warnings, "strict": strict_issues}, ensure_ascii=False))
        sys.exit(1)
    if args.strict and strict_issues:
        print(json.dumps({"errors": strict_issues, "warnings": warnings}, ensure_ascii=False))
        sys.exit(1)

    language = text(data.get("language")) or "ko"
    if language not in LABELS:
        warnings.append(f"지원하지 않는 언어 코드입니다. ko 로 표시합니다: {language}")
        language = "ko"
    labels = LABELS[language]

    auto_notes = []
    short_summary = text(data.get("short_summary"))
    if short_summary:
        short_text = short_summary
    else:
        short_text, truncated = auto_short_summary(data, labels, limits["short"])
        auto_notes.append("short_summary 가 없어 highlights/sections 에서 자동 생성했습니다.")
        if truncated:
            warnings.append(f"short 요약을 {limits['short']}자로 줄였습니다.")
    store_summary = text(data.get("store_summary"))
    if store_summary:
        store_text = store_summary
    else:
        store_text, truncated = auto_store_summary(data, labels, limits["store"])
        auto_notes.append("store_summary 가 없어 sections 에서 자동 생성했습니다.")
        if truncated:
            warnings.append(f"store 요약을 {limits['store']}자로 줄였습니다.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = outdir / f"{args.name}.md"
    html_path = outdir / f"{args.name}.html"
    short_path = outdir / f"{args.name}-short.txt"
    store_path = outdir / f"{args.name}-store.txt"
    internal_path = outdir / f"{args.name}-internal.md"

    md_path.write_text(render_markdown(data, labels), encoding="utf-8")
    html_path.write_text(render_html(data, labels), encoding="utf-8")
    short_path.write_text(short_text.rstrip() + "\n", encoding="utf-8")
    store_path.write_text(store_text.rstrip() + "\n", encoding="utf-8")
    internal_path.write_text(
        render_internal(data, warnings, strict_issues, limits, auto_notes),
        encoding="utf-8",
    )

    commits = data.get("commits") or []
    summary = {
        "md": str(md_path),
        "html": str(html_path),
        "short": str(short_path),
        "store": str(store_path),
        "internal": str(internal_path),
        "sections": len(data.get("sections") or []),
        "highlights": len(data.get("highlights") or []),
        "commits": len(commits),
        "included": sum(1 for commit in commits if commit.get("included", True)),
        "excluded": sum(1 for commit in commits if not commit.get("included", True)),
        "short_chars": len(short_text),
        "short_limit": limits["short"],
        "store_chars": len(store_text),
        "store_limit": limits["store"],
        "auto_summary": bool(auto_notes),
        "warnings": warnings,
        "strict_issues": strict_issues,
    }
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
