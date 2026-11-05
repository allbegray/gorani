"""자기완결 HTML 고지 페이지와 간소화 HTML 렌더러."""

import html
import re

from .constants import PAGE_TITLE
from .model import copyright_line, github_license_url, package_label


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "license"


def license_slugs(groups):
    seen = {}
    slugs = {}
    for group in groups:
        base = slugify(group["license"])
        seen[base] = seen.get(base, 0) + 1
        slugs[group["license"]] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return slugs


def build_simple_html(model):
    metadata = model["meta"]
    packages = model["packages"]
    project = str(metadata.get("project", ""))
    version = str(metadata.get("app_version", ""))
    generated_at = str(metadata.get("generated_at", ""))[:10]
    app_title = " ".join(part for part in (project, version) if part)
    document_title = f"{PAGE_TITLE} — {app_title}" if app_title else PAGE_TITLE
    meta_parts = [app_title] if app_title else []
    if generated_at:
        meta_parts.append(f"Generated {generated_at}")
    meta = " · ".join(meta_parts)
    css = """
:root { color-scheme: light dark; --bg: #fff; --fg: #17181c; --muted: #5c6270; --line: #e2e5ea; --panel: #f6f7f9; --accent: #1f5fbf; }
@media (prefers-color-scheme: dark) { :root { --bg: #111216; --fg: #e8eaee; --muted: #9aa1ae; --line: #2a2d35; --panel: #181a20; --accent: #9db8e8; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif; }
main { max-width: 56rem; margin: 0 auto; padding: 2rem 1.25rem 3rem; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; letter-spacing: -.01em; }
.meta { color: var(--muted); font-size: .875rem; margin: 0 0 1.5rem; }
.wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: .5rem; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: .6rem .75rem; border-bottom: 1px solid var(--line); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
th { background: var(--panel); color: var(--muted); font-size: .8125rem; font-weight: 600; }
td.version { color: var(--muted); white-space: nowrap; }
a { color: var(--accent); }
""".strip()
    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'\">",
        f"<title>{html.escape(document_title)}</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        "<main>",
        f"<h1>{PAGE_TITLE}</h1>",
    ]
    if meta:
        parts.append(f'<p class="meta">{html.escape(meta)}</p>')
    parts.extend(
        [
            '<div class="wrap"><table>',
            "<thead><tr><th>Dependency</th><th>Version</th><th>License</th></tr></thead>",
            "<tbody>",
        ]
    )
    for package in packages:
        name = html.escape(str(package["name"]))
        package_version = html.escape(str(package["version"]))
        url = github_license_url(package)
        link = (
            f'<a href="{html.escape(url, quote=True)}" rel="noopener noreferrer">LICENSE</a>'
            if url
            else "-"
        )
        parts.append(f'<tr><td>{name}</td><td class="version">{package_version}</td><td>{link}</td></tr>')
    parts.extend(["</tbody>", "</table></div>", "</main>", "</body>", "</html>"])
    return "\n".join(parts) + "\n"


def build_html(model):
    meta = model["meta"]
    groups = model["groups"]
    project = str(meta.get("project", ""))
    version = str(meta.get("app_version", ""))
    generated_at = str(meta.get("generated_at", ""))[:10]
    app_title = " ".join(part for part in (project, version) if part)
    document_title = f"{PAGE_TITLE} — {app_title}" if app_title else PAGE_TITLE
    package_count = sum(
        len(variant["packages"]) for group in groups for variant in group["variants"]
    ) + sum(len(group["missing"]) for group in groups)
    license_count = len(groups)
    slugs = license_slugs(groups)
    initial_count = f"{package_count} libraries · {license_count} licenses"
    meta_parts = [app_title] if app_title else []
    if generated_at:
        meta_parts.append(f"Generated {generated_at}")
    meta_parts.append(f"{package_count} libraries")
    meta_line = " · ".join(meta_parts)

    css = """
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #17181c;
  --muted: #5c6270;
  --line: #e2e5ea;
  --panel: #f6f7f9;
  --accent: #1f3864;
  --code: #f3f4f6;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #111216;
    --fg: #e8eaee;
    --muted: #9aa1ae;
    --line: #2a2d35;
    --panel: #181a20;
    --accent: #9db8e8;
    --code: #1a1c22;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Hiragino Sans", "Noto Sans KR", sans-serif;
}
main, header, footer { max-width: 60rem; margin: 0 auto; padding: 0 1.25rem; }
header { padding-top: 2.5rem; padding-bottom: 1rem; }
h1 { font-size: 1.75rem; line-height: 1.25; margin: 0 0 .5rem; letter-spacing: -.01em; }
h2 { font-size: 1.125rem; margin: 0; }
p { margin: .5rem 0; }
.eyebrow { color: var(--accent); font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.meta { color: var(--muted); font-size: .875rem; }
.lede { margin-top: 1rem; max-width: 44rem; }
.controls {
  display: flex; flex-wrap: wrap; align-items: center; gap: .75rem;
  margin: 1.5rem 0 1rem; padding: 1rem; background: var(--panel);
  border: 1px solid var(--line); border-radius: .75rem;
}
.controls label { font-weight: 600; font-size: .875rem; }
.controls input {
  flex: 1 1 16rem; min-width: 0; padding: .55rem .75rem;
  color: var(--fg); background: var(--bg);
  border: 1px solid var(--line); border-radius: .5rem; font: inherit;
}
.controls input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.count { margin: 0; color: var(--muted); font-size: .8125rem; }
.toc { margin: 1.5rem 0 2rem; }
.toc h2 { font-size: .8125rem; color: var(--muted); letter-spacing: .06em; text-transform: uppercase; margin-bottom: .5rem; }
.toc ul { display: flex; flex-wrap: wrap; gap: .5rem; margin: 0; padding: 0; list-style: none; }
.toc a {
  display: inline-flex; gap: .4rem; align-items: baseline;
  padding: .3rem .6rem; color: var(--fg); text-decoration: none;
  background: var(--panel); border: 1px solid var(--line); border-radius: 999px;
  font-size: .8125rem;
}
.toc a:hover { border-color: var(--accent); }
.toc .toc-count { color: var(--muted); font-size: .75rem; }
.license { padding: 1.5rem 0; border-top: 1px solid var(--line); scroll-margin-top: 1rem; }
.license-head { display: flex; align-items: baseline; gap: .6rem; margin-bottom: .75rem; }
.badge {
  padding: .05rem .5rem; color: var(--muted); font-size: .75rem;
  border: 1px solid var(--line); border-radius: 999px;
}
.packages { margin: 0 0 1rem; padding-left: 1.1rem; }
.applies { margin: 0 0 .3rem; color: var(--muted); font-size: .75rem; letter-spacing: .06em; text-transform: uppercase; }
.packages li { margin: .3rem 0; }
.packages .name { font-weight: 600; }
.packages .version { color: var(--muted); font-size: .8125rem; margin-left: .35rem; }
.packages .copyright { display: block; color: var(--muted); font-size: .8125rem; }
details { margin: .75rem 0 0; }
summary {
  cursor: pointer; font-weight: 600; font-size: .875rem;
  padding: .45rem .65rem; background: var(--panel);
  border: 1px solid var(--line); border-radius: .5rem;
}
summary:hover { border-color: var(--accent); }
pre {
  margin: .5rem 0 0; padding: 1rem; overflow: auto;
  white-space: pre-wrap; word-break: break-word;
  background: var(--code); border: 1px solid var(--line); border-radius: .5rem;
  font: .8125rem/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.notice-label { margin: 1rem 0 0; font-weight: 600; font-size: .875rem; }
.variant + .variant { margin-top: 1.25rem; }
.missing { margin-top: 1rem; padding: .75rem 1rem; border: 1px dashed var(--line); border-radius: .5rem; }
.missing p { color: var(--muted); font-size: .875rem; }
.missing ul { margin: .25rem 0 0; padding-left: 1.1rem; font-size: .875rem; }
footer { padding-top: 2rem; padding-bottom: 3rem; color: var(--muted); font-size: .8125rem; border-top: 1px solid var(--line); }
[hidden] { display: none !important; }
@media print {
  .controls, .toc, footer { display: none; }
  details { display: block; }
  details > summary { display: none; }
  details > pre { display: block !important; }
  body { font-size: 11pt; }
  .license { break-inside: avoid-page; }
}
""".strip()

    javascript = """
(function () {
  var input = document.getElementById("search");
  if (!input) return;
  var count = document.getElementById("result-count");
  var sections = Array.prototype.slice.call(document.querySelectorAll("section.license"));
  var links = Array.prototype.slice.call(document.querySelectorAll("nav.toc a"));
  var allItems = Array.prototype.slice.call(document.querySelectorAll("li.package"));
  var initial = count ? count.textContent : "";
  function normalize(value) { return (value || "").toLowerCase(); }
  function apply() {
    var tokens = normalize(input.value).trim().split(/\\s+/).filter(Boolean);
    var visible = 0;
    sections.forEach(function (section) {
      var groupMatch = tokens.length > 0 && tokens.every(function (token) {
        return normalize(section.getAttribute("data-license")).indexOf(token) !== -1;
      });
      var sectionShown = 0;
      var variants = Array.prototype.slice.call(section.querySelectorAll(".variant"));
      variants.forEach(function (variant) {
        var items = Array.prototype.slice.call(variant.querySelectorAll("li.package"));
        var shown = 0;
        items.forEach(function (item) {
          var match = groupMatch || tokens.every(function (token) {
            return normalize(item.getAttribute("data-search")).indexOf(token) !== -1;
          });
          item.hidden = !match;
          if (match) shown += 1;
        });
        variant.hidden = shown === 0;
        var details = variant.querySelectorAll("details");
        for (var i = 0; i < details.length; i += 1) {
          details[i].open = tokens.length > 0 && shown > 0;
        }
        sectionShown += shown;
      });
      section.hidden = sectionShown === 0;
      var badge = section.querySelector(".badge");
      if (badge) {
        badge.textContent = tokens.length === 0 ? badge.getAttribute("data-total") : sectionShown;
      }
      visible += sectionShown;
    });
    links.forEach(function (link) {
      var target = document.querySelector(link.getAttribute("href"));
      var row = link.parentNode;
      row.hidden = !!(target && target.hidden);
      var countLabel = link.querySelector(".toc-count");
      if (countLabel && target) {
        countLabel.textContent = tokens.length === 0
          ? link.getAttribute("data-total")
          : target.querySelectorAll("li.package:not([hidden])").length;
      }
    });
    if (count) {
      count.textContent = tokens.length === 0
        ? initial
        : visible + " of " + allItems.length + " libraries shown";
    }
  }
  input.addEventListener("input", apply);
})();
""".strip()

    parts = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'\">",
        f"<title>{html.escape(document_title)}</title>",
        f"<style>\n{css}\n</style>",
        "</head>",
        "<body>",
        "<header>",
        '<p class="eyebrow">Open source notices</p>',
        f"<h1>{PAGE_TITLE}</h1>",
        f'<p class="meta">{html.escape(meta_line)}</p>',
        '<p class="lede">This product includes the third-party software listed below. '
        "Each license text and copyright notice is reproduced for attribution. "
        "Where libraries share the same license, the text appears once and each "
        "copyright notice is listed with its library.</p>",
        "</header>",
        "<main>",
        '<div class="controls">',
        '<label for="search">Search libraries</label>',
        '<input id="search" type="search" placeholder="Library, version, or license" '
        'autocomplete="off" spellcheck="false">',
        f'<p class="count" id="result-count" aria-live="polite">{html.escape(initial_count)}</p>',
        "</div>",
        "<noscript><p class=\"count\">Search needs JavaScript. All licenses are listed below.</p></noscript>",
        '<nav class="toc" aria-label="License index">',
        "<h2>Licenses</h2>",
        "<ul>",
    ]
    for group in groups:
        slug = slugs[group["license"]]
        count = sum(len(variant["packages"]) for variant in group["variants"]) + len(
            group["missing"]
        )
        parts.append(
            f'<li><a href="#license-{slug}" data-total="{count}">{html.escape(group["license"])}'
            f'<span class="toc-count">{count}</span></a></li>'
        )
    parts.extend(["</ul>", "</nav>"])

    for group in groups:
        slug = slugs[group["license"]]
        count = sum(len(variant["packages"]) for variant in group["variants"]) + len(
            group["missing"]
        )
        parts.append(
            f'<section class="license" id="license-{slug}" '
            f'data-license="{html.escape(group["license"], quote=True)}">'
        )
        parts.append(
            f'<div class="license-head"><h2>{html.escape(group["license"])}</h2>'
            f'<span class="badge" data-total="{count}">{count}</span></div>'
        )
        for index, variant in enumerate(group["variants"], start=1):
            parts.append('<div class="variant">')
            parts.append('<p class="applies">Applies to</p>')
            parts.append('<ul class="packages">')
            for package in variant["packages"]:
                search_value = " ".join(
                    part
                    for part in (
                        package["name"],
                        package["version"],
                        group["license"],
                        copyright_line(package),
                    )
                    if part
                )
                parts.append(
                    f'<li class="package" data-search="{html.escape(search_value.lower(), quote=True)}">'
                    f'<span class="name">{html.escape(package["name"])}</span>'
                )
                if package["version"]:
                    parts.append(
                        f'<span class="version">{html.escape(package["version"])}</span>'
                    )
                notice = copyright_line(package)
                if notice:
                    parts.append(f'<span class="copyright">{html.escape(notice)}</span>')
                parts.append("</li>")
            parts.append("</ul>")
            label = "License text" if len(group["variants"]) == 1 else f"License text {index}"
            parts.append(
                f"<details><summary>{label}</summary>"
                f"<pre tabindex=\"0\">{html.escape(variant['text'].rstrip())}</pre>"
            )
            seen_notices = []
            for package in variant["packages"]:
                notice_text = package.get("notice_text", "").strip()
                if notice_text and notice_text not in seen_notices:
                    seen_notices.append(notice_text)
            for notice_text in seen_notices:
                parts.append(
                    '<p class="notice-label">NOTICE</p>'
                    f"<pre tabindex=\"0\">{html.escape(notice_text.rstrip())}</pre>"
                )
            parts.append("</details>")
            parts.append("</div>")
        if group["missing"]:
            parts.append('<div class="variant missing"><p>License text not found for:</p><ul>')
            for package in group["missing"]:
                parts.append(
                    f'<li class="package" data-search="{html.escape((package_label(package) + " " + group["license"]).lower(), quote=True)}">'
                    f"{html.escape(package_label(package))}</li>"
                )
            parts.append("</ul></div>")
        parts.append("</section>")

    parts.extend(
        [
            "</main>",
            "<footer>Generated from the project SBOM. License texts are reproduced verbatim "
            "from the package sources.</footer>",
            f"<script>\n{javascript}\n</script>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(parts) + "\n"
