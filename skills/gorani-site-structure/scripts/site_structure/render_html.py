"""HTML 렌더러. 리포트 모델을 자기완결 검색형 HTML로 만든다."""

import html

from .constants import REVIEW_QUESTIONS, STATUSES
from .model import bool_label, build_menu_tree, table_label


def build_html(model):
    meta = model["meta"]
    pages = model["pages"]
    summary = model["summary"]
    depth_count = summary["depth"]
    warnings = model["warnings"]
    standards = model["standards"]
    api_only = model["api_only"]
    document_title = f"사이트 구조도 — {meta['site']}"
    review_questions = "".join(f"<li>{html.escape(question)}</li>" for question in REVIEW_QUESTIONS)
    tree = build_menu_tree(pages)

    def badge(value):
        return html.escape(value or "-")

    def render_tree(node):
        parts = []
        for label, child in node["children"].items():
            parts.append(f'<li class="menu-node"><span class="menu-label">{html.escape(label)}</span><ul>')
            parts.extend(render_tree(child))
            parts.append("</ul></li>")
        for page in node["pages"]:
            search = " ".join([page["title"], " ".join(page["menu_path"]), page["url"], page["exposure"]]).lower()
            parts.append(
                f'<li class="screen-item" data-tree-search="{html.escape(search, quote=True)}">'
                f'<a href="#screen-{html.escape(page["id"], quote=True)}">{html.escape(page["title"])}</a>'
                f'<span class="badge">{badge(page["exposure"])}</span>'
                f'<span class="path">{html.escape(page["url"] or "-")}</span></li>'
            )
        return parts

    tree_html = "".join(render_tree(tree))
    css = """
:root { color-scheme: light dark; --bg:#fff; --fg:#17181c; --muted:#5c6270; --line:#e2e5ea; --panel:#f6f7f9; --accent:#1f5fbf; }
@media (prefers-color-scheme: dark) { :root { --bg:#111216; --fg:#e8eaee; --muted:#9aa1ae; --line:#2a2d35; --panel:#181a20; --accent:#9db8e8; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR",sans-serif; }
main, header, footer { max-width:86rem; margin:0 auto; padding:0 1.25rem; }
header { padding-top:2.5rem; }
h1 { font-size:1.8rem; margin:0 0 .35rem; letter-spacing:-.02em; }
h2 { font-size:1.15rem; margin:0 0 .75rem; }
h3 { font-size:.95rem; margin:1rem 0 .5rem; }
p { margin:.35rem 0; }
.eyebrow { color:var(--accent); font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
.meta { color:var(--muted); font-size:.875rem; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(9rem,1fr)); gap:.65rem; margin:1.5rem 0 1rem; }
.stat { padding:.75rem .9rem; background:var(--panel); border:1px solid var(--line); border-radius:.6rem; }
.stat strong { display:block; font-size:1.25rem; }
.stat span { color:var(--muted); font-size:.78rem; }
.controls { display:flex; flex-wrap:wrap; align-items:center; gap:.75rem; margin:1.2rem 0 .8rem; padding:.85rem 1rem; background:var(--panel); border:1px solid var(--line); border-radius:.7rem; }
.controls label { font-weight:600; font-size:.875rem; }
.controls input { flex:1 1 16rem; min-width:0; padding:.55rem .75rem; color:var(--fg); background:var(--bg); border:1px solid var(--line); border-radius:.45rem; font:inherit; }
.controls input:focus-visible { outline:2px solid var(--accent); outline-offset:1px; }
.count { color:var(--muted); font-size:.8125rem; }
.tree { margin:0; padding:1rem 1rem 1rem 1.4rem; background:var(--panel); border:1px solid var(--line); border-radius:.6rem; }
.tree ul { margin:.25rem 0 .25rem 1rem; padding-left:1rem; border-left:1px solid var(--line); }
.tree li { margin:.3rem 0; }
.menu-label { font-weight:700; }
.menu-node > .menu-label { color:var(--fg); }
.screen-item a { color:var(--accent); text-decoration:none; }
.screen-item a:hover { text-decoration:underline; }
.badge { display:inline-block; margin-left:.45rem; padding:.02rem .4rem; color:var(--muted); border:1px solid var(--line); border-radius:999px; font-size:.7rem; }
.path { margin-left:.45rem; color:var(--muted); font: .75rem/1.3 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }
.section { margin:1.5rem 0; }
.table-wrap { overflow-x:auto; border:1px solid var(--line); border-radius:.5rem; }
table { width:100%; border-collapse:collapse; font-size:.84rem; }
th, td { padding:.5rem .6rem; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
tr:last-child td { border-bottom:0; }
th { background:var(--panel); color:var(--muted); font-size:.76rem; font-weight:600; white-space:nowrap; }
.status { display:inline-block; padding:.02rem .4rem; border-radius:999px; font-size:.72rem; }
.status.active { background:#C6E0B4; color:#1e3b12; }
.status.planned { background:#FFE699; color:#4d3b00; }
.status.deprecated { background:#D9D9D9; color:#333; }
.warnings { padding:1rem; border:1px dashed var(--line); border-radius:.6rem; }
.warnings ul { margin:.25rem 0 0; padding-left:1.2rem; color:var(--muted); font-size:.875rem; }
.links a { color:var(--accent); }
footer { padding:2rem 0 3rem; color:var(--muted); font-size:.8125rem; border-top:1px solid var(--line); }
[hidden] { display:none !important; }
@media print { .controls, footer { display:none; } .section { break-inside:avoid-page; } body { font-size:10.5pt; } }
""".strip()
    javascript = """
(function () {
  var input = document.getElementById("search");
  if (!input) return;
  var count = document.getElementById("result-count");
  var rows = Array.prototype.slice.call(document.querySelectorAll("[data-screen-search]"));
  var treeItems = Array.prototype.slice.call(document.querySelectorAll("[data-tree-search]"));
  var menus = Array.prototype.slice.call(document.querySelectorAll(".menu-node")).reverse();
  function apply() {
    var q = (input.value || "").trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (item) {
      var match = !q || (item.getAttribute("data-screen-search") || "").indexOf(q) !== -1;
      item.hidden = !match;
      if (match) shown += 1;
    });
    treeItems.forEach(function (item) {
      var match = !q || (item.getAttribute("data-tree-search") || "").indexOf(q) !== -1;
      item.hidden = !match;
    });
    menus.forEach(function (menu) {
      var has = menu.querySelector("[data-tree-search]:not([hidden])");
      menu.hidden = !has;
    });
    if (count) count.textContent = q ? shown + " matches" : shown + " screens";
  }
  input.addEventListener("input", apply);
  apply();
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
        '<p class="eyebrow">Information architecture</p>',
        f"<h1>{html.escape(document_title)}</h1>",
        f'<p class="meta">{html.escape(meta["site"])} · {html.escape(meta["inspected_at"] or "-")} · {html.escape(meta["source"] or "-")}</p>',
        f'<p class="meta">역할: {html.escape(", ".join(meta["roles"]) or "-")} · 화면 폭: {html.escape(", ".join(meta["viewports"]) or "-")}</p>',
        '<div class="stats">',
        f'<div class="stat"><strong>{summary["pages"]}</strong><span>화면</span></div>',
        f'<div class="stat"><strong>{summary["menu_groups"]}</strong><span>메뉴 그룹</span></div>',
        f'<div class="stat"><strong>{summary["api_mappings"]}</strong><span>API 매핑</span></div>',
        f'<div class="stat"><strong>{len(api_only)}</strong><span>API only</span></div>',
        "</div>",
        "</header>",
        "<main>",
        f'<div class="controls"><label for="search">화면 검색</label><input id="search" type="search" placeholder="메뉴·화면·URL" autocomplete="off"><p class="count" id="result-count">{summary["pages"]} screens</p></div>',
        '<section class="section"><h2>메뉴 구조</h2><ul class="tree">',
        tree_html,
        "</ul></section>",
        '<section class="section"><h2>화면 목록</h2><div class="table-wrap"><table>',
        "<thead><tr><th>화면</th><th>메뉴 경로</th><th>URL</th><th>부모 화면</th><th>레이아웃</th><th>노출</th><th>역할</th><th>데스크톱</th><th>모바일</th><th>상태</th><th>스크린샷 경로</th></tr></thead><tbody>",
    ]
    for page in pages:
        search = " ".join([page["title"], " ".join(page["menu_path"]), page["url"], page["exposure"]]).lower()
        status_class = page["status"] if page["status"] in STATUSES else "active"
        parts.append(
            f'<tr id="screen-{html.escape(page["id"], quote=True)}" data-screen-search="{html.escape(search, quote=True)}">'
            f"<td><strong>{html.escape(page['title'])}</strong><br><span class=path>{html.escape(page['id'])}</span></td>"
            f"<td>{html.escape(table_label(page))}</td>"
            f"<td>{html.escape(page['url'] or '-')}</td>"
            f"<td>{html.escape(page['parent_title'] or '-')}</td>"
            f"<td>{html.escape(page['layout'] or '-')}</td>"
            f"<td>{html.escape(page['exposure'])}</td>"
            f"<td>{html.escape(', '.join(page['roles']))}</td>"
            f"<td>{bool_label(page['desktop'])}</td><td>{bool_label(page['mobile'])}</td>"
            f'<td><span class="status {status_class}">{html.escape(page["status"])}</span></td>'
            f"<td>{html.escape(page['screenshot'] or '-')}</td>"
            "</tr>"
        )
    parts += ["</tbody></table></div></section>", '<section class="section"><h2>API only</h2>']
    if api_only:
        parts += ["<div class=table-wrap><table><thead><tr><th>Method</th><th>API 경로</th><th>용도</th><th>호출 주체</th><th>화면 없음 사유</th></tr></thead><tbody>"]
        for api in api_only:
            parts.append(
                f"<tr><td>{html.escape(api['method'])}</td><td>{html.escape(api['path'])}</td><td>{html.escape(api['purpose'] or '-')}</td><td>{html.escape(api['caller'] or '-')}</td><td>{html.escape(api['reason'] or '-')}</td></tr>"
            )
        parts.append("</tbody></table></div>")
    else:
        parts.append("<p>API only 없음</p>")
    parts += ['</section><section class="section links"><h2>표준 근거</h2>']
    if standards:
        parts += ["<div class=table-wrap><table><thead><tr><th>구분</th><th>문서</th><th>적용 항목</th><th>내용</th><th>링크</th></tr></thead><tbody>"]
        for standard in standards:
            link = f'<a href="{html.escape(standard["url"], quote=True)}" rel="noopener noreferrer">{html.escape(standard["name"])}</a>' if standard["url"] else html.escape(standard["name"])
            parts.append(
                f"<tr><td>{html.escape(standard['source'] or '-')}</td><td>{link}</td><td>{html.escape(standard['scope'] or '-')}</td><td>{html.escape(standard['rule'] or '-')}</td><td>{html.escape(standard['url'] or '-')}</td></tr>"
            )
        parts.append("</tbody></table></div>")
    else:
        parts.append("<p>표준 근거 없음</p>")
    parts += ["</section>", '<section class="section warnings"><h2>검토 메모</h2>']
    if warnings:
        parts.append("<ul>")
        for warning in warnings:
            parts.append(
                f"<li><strong>{html.escape(warning['category'])}</strong>: {html.escape(warning['message'])}"
                + (f" — {html.escape(warning['action'])}" if warning["action"] else "")
                + "</li>"
            )
        parts.append("</ul>")
    else:
        parts.append("<p>검토 메모 없음</p>")
    parts += [
        "</section>",
        '<section class="section"><h2>검토 요청</h2><ol>',
        review_questions,
        "</ol></section>",
        "</main>",
        f"<footer>생성 기준: {html.escape(meta['source'] or '-')} · 적용 기준: {html.escape(meta['standard'] or '-')} · Depth {depth_count} (최소 2, KRDS 최대 3 권장)</footer>",
        f"<script>{javascript}</script>",
        "</body>",
        "</html>",
    ]
    return "\n".join(parts) + "\n"
