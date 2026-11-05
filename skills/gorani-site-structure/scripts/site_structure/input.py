"""사이트 구조 입력 JSON을 읽고 페이지·표준·검토 메모를 정규화한다."""

import json
import re
import sys
from pathlib import Path

from .constants import STATUSES


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_menu_path(value, title):
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
    else:
        text = str(value or "").strip()
        parts = [item.strip() for item in re.split(r"\s*>\s*", text) if item.strip()]
    return parts or [title]


def normalize_roles(value):
    if isinstance(value, list):
        values = [str(item).strip() for item in value if str(item).strip()]
    else:
        values = [item.strip() for item in str(value or "").split(",") if item.strip()]
    return values or ["전체"]


def normalize_bool(value, default=True):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"y", "yes", "true", "1", "예"}:
        return True
    if text in {"n", "no", "false", "0", "아니오"}:
        return False
    return default


def normalize_api(raw):
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        parts = text.split(None, 1)
        method = parts[0].upper()
        path = parts[1] if len(parts) > 1 else ""
        return {"method": method, "path": path, "purpose": "", "when": "", "note": ""}
    if not isinstance(raw, dict):
        return None
    method = str(raw.get("method", "")).strip().upper()
    path = str(raw.get("path", "")).strip()
    if not method or not path:
        return None
    return {
        "method": method,
        "path": path,
        "purpose": str(raw.get("purpose", "")).strip(),
        "when": str(raw.get("when", "")).strip(),
        "note": str(raw.get("note", "")).strip(),
    }


def load_input(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_pages = data.get("pages")
    if not isinstance(raw_pages, list) or not raw_pages:
        sys.exit("입력 JSON의 pages 배열이 비어 있습니다.")
    pages = []
    ids = set()
    for raw in raw_pages:
        if not isinstance(raw, dict):
            continue
        page_id = str(raw.get("id", "")).strip()
        if not page_id:
            sys.exit("page.id 는 필수입니다.")
        if page_id in ids:
            sys.exit(f"page.id 가 중복됐습니다: {page_id}")
        ids.add(page_id)
        title = str(raw.get("title", "")).strip() or page_id
        status = str(raw.get("status", "active")).strip().lower() or "active"
        if status not in STATUSES:
            sys.exit(f"page.status 는 active/planned/deprecated 중 하나여야 합니다: {page_id}")
        apis = [api for api in (normalize_api(item) for item in raw.get("apis", []) or []) if api]
        pages.append(
            {
                "id": page_id,
                "title": title,
                "menu_path": normalize_menu_path(raw.get("menu_path"), title),
                "parent_id": str(raw.get("parent_id", "")).strip(),
                "url": str(raw.get("url", "")).strip(),
                "layout": str(raw.get("layout", "")).strip(),
                "roles": normalize_roles(raw.get("roles")),
                "exposure": str(raw.get("exposure", "")).strip() or "미확인",
                "desktop": normalize_bool(raw.get("desktop"), True),
                "mobile": normalize_bool(raw.get("mobile"), True),
                "status": status,
                "screenshot": str(raw.get("screenshot", "")).strip(),
                "apis": apis,
                "source": str(raw.get("source", "")).strip(),
                "note": str(raw.get("note", "")).strip(),
            }
        )
    if not pages:
        sys.exit("정규화된 page가 없습니다.")

    page_map = {page["id"]: page for page in pages}
    warnings = []
    for raw in data.get("warnings", []) or []:
        if isinstance(raw, dict) and str(raw.get("message", "")).strip():
            warnings.append(
                {
                    "category": str(raw.get("category", "검토")).strip() or "검토",
                    "message": str(raw.get("message", "")).strip(),
                    "action": str(raw.get("action", "")).strip(),
                }
            )
    depth_count = max(2, max(len(page["menu_path"]) for page in pages))
    if depth_count > 3:
        warnings.append(
            {
                "category": "KRDS",
                "message": f"메뉴 depth가 {depth_count}수준입니다. KRDS 메인 메뉴는 최대 3수준을 권장합니다.",
                "action": "3Depth 초과 항목을 메뉴가 아닌 상세·탭·액션 화면으로 분리하세요.",
            }
        )
    for page in pages:
        page["parent_title"] = ""
        if page["parent_id"]:
            parent = page_map.get(page["parent_id"])
            if parent is None:
                warnings.append(
                    {
                        "category": "구조",
                        "message": f"{page['id']}의 parent_id가 없습니다: {page['parent_id']}",
                        "action": "부모 화면 ID를 확인하세요.",
                    }
                )
            else:
                page["parent_title"] = parent["title"]
        if page["status"] == "active" and not page["screenshot"]:
            warnings.append(
                {
                    "category": "증적",
                    "message": f"{page['id']}의 스크린샷 경로가 없습니다.",
                    "action": "실제 화면을 캡처해 screens/ 아래에 저장하세요.",
                }
            )
    standards = []
    for raw in data.get("standards", []) or []:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name", "")).strip()
        if not name:
            continue
        standards.append(
            {
                "source": str(raw.get("source", "")).strip(),
                "name": name,
                "scope": str(raw.get("scope", "")).strip(),
                "rule": str(raw.get("rule", "")).strip(),
                "url": str(raw.get("url", "")).strip(),
            }
        )
    api_only = []
    for raw in data.get("api_only", []) or []:
        api = normalize_api(raw)
        if api:
            api["caller"] = str(raw.get("caller", "")).strip()
            api["reason"] = str(raw.get("reason", "")).strip()
            api_only.append(api)

    meta = {
        "site": str(data.get("site", "")).strip() or "Site",
        "base_url": str(data.get("base_url", "")).strip(),
        "inspected_at": str(data.get("inspected_at", "")).strip(),
        "source": str(data.get("source", "")).strip(),
        "standard": str(data.get("standard", "")).strip(),
        "roles": as_list(data.get("roles")),
        "viewports": as_list(data.get("viewports")),
        "review_status": str(data.get("review_status", "")).strip(),
        "sources": as_list(data.get("sources")),
    }
    return meta, pages, depth_count, warnings, standards, api_only
