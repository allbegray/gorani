"""릴리스 노트를 자기완결 HTML로 렌더링한다."""

import html

from .constants import LABELS
from .model import safe_href, text


def render_html(model, labels=None):
    data = model.get("content", model)
    if labels is None:
        labels = LABELS[model["meta"]["language"]]
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
