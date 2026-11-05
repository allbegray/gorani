"""테이블 명세서를 자기완결 HTML로 렌더링한다."""

import html

from .render_md import table_label


def build_html(model):
    meta = model.get("meta", {})
    summary = model.get("summary", {})
    tables = model.get("tables", [])
    warnings = model.get("warnings", [])
    project = str(meta.get("project", ""))
    generated_at = str(meta.get("generated_at", ""))
    source_label = str(meta.get("source_label", ""))
    dialect = ", ".join(meta.get("dialects") or [])
    document_title = f"테이블 명세서 — {project}" if project else "테이블 명세서"

    def value(raw):
        text = "" if raw is None else str(raw)
        return html.escape(text or "-")

    def flag(active, label="Y"):
        if active:
            return f'<span class="flag yes">{html.escape(label)}</span>'
        return '<span class="flag">-</span>'

    stats = [
        ("테이블", len(tables)),
        ("컬럼", summary.get("columns", 0)),
        ("관계", summary.get("foreign_keys", 0)),
        ("인덱스", summary.get("indexes", 0)),
    ]
    css = """
:root {
  color-scheme: light dark;
  --bg: #ffffff;
  --fg: #17181c;
  --muted: #5c6270;
  --line: #e2e5ea;
  --panel: #f6f7f9;
  --accent: #1f5fbf;
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
body { margin: 0; background: var(--bg); color: var(--fg); font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif; }
main, header, footer { max-width: 78rem; margin: 0 auto; padding: 0 1.25rem; }
header { padding-top: 2.5rem; padding-bottom: .5rem; }
h1 { font-size: 1.8rem; line-height: 1.2; margin: 0 0 .4rem; letter-spacing: -.02em; }
h2 { font-size: 1.15rem; margin: 0; }
h3 { font-size: .95rem; margin: 0 0 .5rem; }
p { margin: .35rem 0; }
.eyebrow { color: var(--accent); font-size: .72rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
.meta { color: var(--muted); font-size: .875rem; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: .65rem; margin: 1.5rem 0 1rem; }
.stat { padding: .75rem .9rem; background: var(--panel); border: 1px solid var(--line); border-radius: .6rem; }
.stat strong { display: block; font-size: 1.25rem; line-height: 1.2; }
.stat span { color: var(--muted); font-size: .78rem; }
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: .75rem; margin: 1.2rem 0 .8rem; padding: .85rem 1rem; background: var(--panel); border: 1px solid var(--line); border-radius: .7rem; }
.controls label { font-weight: 600; font-size: .875rem; }
.controls input { flex: 1 1 16rem; min-width: 0; padding: .55rem .75rem; color: var(--fg); background: var(--bg); border: 1px solid var(--line); border-radius: .45rem; font: inherit; }
.controls input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.count { margin: 0; color: var(--muted); font-size: .8125rem; }
.toc { margin: .8rem 0 1.5rem; }
.toc ul { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0; padding: 0; list-style: none; }
.toc a { display: inline-flex; padding: .28rem .6rem; color: var(--fg); background: var(--panel); border: 1px solid var(--line); border-radius: 999px; font-size: .8rem; text-decoration: none; }
.toc a:hover { border-color: var(--accent); }
.overview { margin: 1.5rem 0 2rem; }
.table-card { padding: 1.5rem 0; border-top: 1px solid var(--line); scroll-margin-top: 1rem; }
.table-card h2 { display: flex; flex-wrap: wrap; align-items: baseline; gap: .5rem; }
.table-card h2 .desc { color: var(--muted); font-size: .9rem; font-weight: 400; }
.table-card .meta { margin-bottom: .75rem; }
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: .5rem; }
table { width: 100%; border-collapse: collapse; font-size: .84rem; }
th, td { padding: .5rem .6rem; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
tr:last-child td { border-bottom: 0; }
th { background: var(--panel); color: var(--muted); font-size: .76rem; font-weight: 600; white-space: nowrap; }
tbody tr:nth-child(even) td { background: color-mix(in srgb, var(--panel) 55%, transparent); }
.flag { color: var(--muted); }
.flag.yes { color: var(--accent); font-weight: 700; }
.subsection { margin-top: 1rem; }
.warnings { margin: 1.5rem 0; padding: 1rem; border: 1px dashed var(--line); border-radius: .6rem; }
.warnings h2 { font-size: 1rem; margin-bottom: .4rem; }
.warnings ul { margin: .25rem 0 0; padding-left: 1.2rem; color: var(--muted); font-size: .875rem; }
footer { padding-top: 2rem; padding-bottom: 2.5rem; color: var(--muted); font-size: .8125rem; border-top: 1px solid var(--line); }
[hidden] { display: none !important; }
@media print {
  .controls, .toc, footer { display: none; }
  .table-card { break-inside: avoid-page; }
  body { font-size: 10.5pt; }
}
""".strip()
    javascript = """
(function () {
  var input = document.getElementById("search");
  if (!input) return;
  var count = document.getElementById("result-count");
  var cards = Array.prototype.slice.call(document.querySelectorAll(".table-card"));
  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  var initial = count ? count.textContent : "";
  function apply() {
    var query = (input.value || "").trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {
      var match = !query || (card.getAttribute("data-search") || "").indexOf(query) !== -1;
      card.hidden = !match;
      if (match) shown += 1;
    });
    links.forEach(function (link) {
      var target = document.querySelector(link.getAttribute("href"));
      link.parentNode.hidden = !!(target && target.hidden);
    });
    if (count) {
      count.textContent = query ? shown + " / " + cards.length + " tables" : initial;
    }
  }
  input.addEventListener("input", apply);
})();
""".strip()
    parts = [
        "<!doctype html>",
        '<html lang="ko">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'\">",
        f"<title>{html.escape(document_title)}</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        "<header>",
        '<p class="eyebrow">Database specification</p>',
        f"<h1>{html.escape(document_title)}</h1>",
        f'<p class="meta">{html.escape(project or "-")} · {html.escape(generated_at)}</p>',
        f'<p class="meta">원본: {html.escape(source_label or "-")} · SQL 방언: {html.escape(dialect or "-")}</p>',
        '<div class="stats">',
    ]
    for label, count in stats:
        parts.append(f'<div class="stat"><strong>{count}</strong><span>{html.escape(label)}</span></div>')
    parts.extend(
        [
            "</div>",
            "</header>",
            "<main>",
            '<div class="controls">',
            '<label for="search">테이블 검색</label>',
            '<input id="search" type="search" placeholder="테이블·컬럼·설명" autocomplete="off" spellcheck="false">',
            f'<p class="count" id="result-count" aria-live="polite">{len(tables)} tables</p>',
            "</div>",
            '<nav class="toc" aria-label="테이블 목차"><ul>',
        ]
    )
    for index, table in enumerate(tables, start=1):
        parts.append(
            f'<li><a href="#table-{index}">{html.escape(table_label(table))}</a></li>'
        )
    parts.extend(["</ul></nav>", '<section class="overview"><h2>테이블 목록</h2><div class="table-wrap"><table>'])
    parts.append(
        "<thead><tr><th>No</th><th>스키마</th><th>테이블</th><th>설명</th><th>컬럼</th><th>PK</th><th>FK</th><th>인덱스</th></tr></thead><tbody>"
    )
    for index, table in enumerate(tables, start=1):
        parts.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{value(table['schema'] or '-')}</td>"
            f'<td><a href="#table-{index}">{value(table["name"])}</a></td>'
            f"<td>{value(table['description'] or '-')}</td>"
            f"<td>{len(table['columns'])}</td>"
            f"<td>{value(', '.join(table['primary_key']) or '-')}</td>"
            f"<td>{len(table['foreign_keys'])}</td>"
            f"<td>{len(table['indexes'])}</td>"
            "</tr>"
        )
    parts.append("</tbody></table></div></section>")

    for index, table in enumerate(tables, start=1):
        search_text = " ".join(
            [
                table_label(table),
                table["description"],
                " ".join(column["name"] for column in table["columns"]),
                " ".join(column["comment"] for column in table["columns"]),
            ]
        ).lower()
        parts.extend(
            [
                f'<section class="table-card" id="table-{index}" data-search="{html.escape(search_text, quote=True)}">',
                f"<h2>{html.escape(table['name'])}"
                + (f' <span class="desc">{html.escape(table["description"])}</span>' if table["description"] else "")
                + "</h2>",
                f'<p class="meta">스키마: {html.escape(table["schema"] or "-")}'
                + (f" · 원본: {html.escape(', '.join(table['source_files']))}" if table["source_files"] else "")
                + "</p>",
                '<div class="table-wrap"><table>',
                "<thead><tr><th>No</th><th>컬럼</th><th>타입</th><th>길이</th><th>PK</th><th>FK</th><th>UNIQUE</th><th>NOT NULL</th><th>DEFAULT</th><th>설명</th><th>비고</th></tr></thead><tbody>",
            ]
        )
        for column_index, column in enumerate(table["columns"], start=1):
            parts.append(
                "<tr>"
                f"<td>{column_index}</td>"
                f"<td>{value(column['name'])}</td>"
                f"<td>{value(column['data_type'])}</td>"
                f"<td>{value(column['length'] or '-')}</td>"
                f"<td>{flag(column['primary_key'])}</td>"
                f"<td>{flag(column['references'])}</td>"
                f"<td>{flag(column['unique'])}</td>"
                f"<td>{flag(not column['nullable'])}</td>"
                f"<td>{value(column['default'] or '-')}</td>"
                f"<td>{value(column['comment'] or '-')}</td>"
                f"<td>{value(column['note'] or '-')}</td>"
                "</tr>"
            )
        parts.append("</tbody></table></div>")

        if table["foreign_keys"]:
            parts.extend(
                [
                    '<div class="subsection"><h3>관계</h3><div class="table-wrap"><table>',
                    "<thead><tr><th>FK</th><th>컬럼</th><th>참조 테이블</th><th>참조 컬럼</th><th>ON DELETE</th><th>ON UPDATE</th></tr></thead><tbody>",
                ]
            )
            for foreign_key in table["foreign_keys"]:
                ref_table = (
                    f"{foreign_key['ref_schema']}.{foreign_key['ref_table']}"
                    if foreign_key["ref_schema"]
                    else foreign_key["ref_table"]
                )
                parts.append(
                    "<tr>"
                    f"<td>{value(foreign_key['name'])}</td>"
                    f"<td>{value(', '.join(foreign_key['columns']) or '-')}</td>"
                    f"<td>{value(ref_table or '-')}</td>"
                    f"<td>{value(', '.join(foreign_key['ref_columns']) or '-')}</td>"
                    f"<td>{value(foreign_key['on_delete'] or '-')}</td>"
                    f"<td>{value(foreign_key['on_update'] or '-')}</td>"
                    "</tr>"
                )
            parts.append("</tbody></table></div></div>")

        if table["indexes"]:
            parts.extend(
                [
                    '<div class="subsection"><h3>인덱스</h3><div class="table-wrap"><table>',
                    "<thead><tr><th>인덱스</th><th>UNIQUE</th><th>컬럼</th></tr></thead><tbody>",
                ]
            )
            for index_entry in table["indexes"]:
                parts.append(
                    "<tr>"
                    f"<td>{value(index_entry['name'])}</td>"
                    f"<td>{flag(index_entry['unique'])}</td>"
                    f"<td>{value(', '.join(index_entry['columns']) or '-')}</td>"
                    "</tr>"
                )
            parts.append("</tbody></table></div></div>")
        parts.append("</section>")

    if warnings:
        parts.extend(['<section class="warnings"><h2>파싱 메모</h2><ul>'])
        for warning in warnings:
            parts.append(f"<li>{html.escape(warning)}</li>")
        parts.append("</ul></section>")
    parts.extend(
        [
            "</main>",
            f"<footer>원본: {html.escape(source_label or '-')} · 생성: {html.escape(generated_at)}</footer>",
            f"<script>{javascript}</script>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(parts) + "\n"
