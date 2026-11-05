"""정규화된 페이지를 렌더러가 소비하는 리포트 모델로 만든다."""

from collections import Counter

from .constants import SCHEMA_VERSION


def table_label(page):
    return " > ".join(page["menu_path"])


def status_counts(pages):
    return Counter(page["status"] for page in pages)


def api_count(pages):
    return sum(len(page["apis"]) for page in pages)


def bool_label(value):
    return "Y" if value else "N"


def build_menu_tree(pages):
    root = {"label": "", "children": {}, "pages": []}
    for page in pages:
        node = root
        for label in page["menu_path"]:
            node = node["children"].setdefault(label, {"label": label, "children": {}, "pages": []})
        node["pages"].append(page)
    return root


def build_report_model(
    meta,
    pages,
    depth_count,
    warnings,
    standards,
    api_only,
    sources,
    generated_at,
):
    counts = status_counts(pages)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "meta": dict(meta),
        "summary": {
            "pages": len(pages),
            "depth": depth_count,
            "menu_groups": len({page["menu_path"][0] for page in pages}),
            "status": {
                status: counts.get(status, 0)
                for status in ("active", "planned", "deprecated")
            },
            "api_mappings": api_count(pages),
            "api_only": len(api_only),
            "standards": len(standards),
            "warnings": len(warnings),
        },
        "pages": pages,
        "api_only": api_only,
        "standards": standards,
        "warnings": warnings,
        "sources": list(sources),
    }
