#!/usr/bin/env python3
"""Compare two OpenAPI 3.x specs and write a contract-change report.

Usage:
    python3 api_diff.py --old old.yaml --new new.yaml --out api-diff.md
    python3 api_diff.py --old old.json --new new.json --json-out api-diff.json
    python3 api_diff.py --old old.yaml --new new.yaml --fail-on-breaking

The report is a spec-level comparison. Runtime behavior, gateway policy, and
client implementation still need confirmation.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


METHODS = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]
SEVERITIES = ["breaking", "risky", "non-breaking", "info"]
PREFIXES = {"breaking": "B", "risky": "R", "non-breaking": "N", "info": "I"}
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
PRIORITY_LABELS = {
    "P0": "전면 중단",
    "P1": "배포 전 수정",
    "P2": "배포 전 확인",
    "P3": "호환성 확인",
    "P4": "참고",
}


def parse_args():
    parser = argparse.ArgumentParser(description="OpenAPI 3.x 계약 변경 리포트")
    parser.add_argument("--old", required=True, help="이전 OpenAPI 스펙 (JSON/YAML)")
    parser.add_argument("--new", required=True, help="새 OpenAPI 스펙 (JSON/YAML)")
    parser.add_argument("--out", default="api-diff.md", help="Markdown 출력 경로. '-' 이면 stdout")
    parser.add_argument("--json-out", help="findings JSON 출력 경로")
    parser.add_argument("--service", default="", help="서비스명")
    parser.add_argument("--release-version", default="", help="배포 버전")
    parser.add_argument("--clients", default="", help="영향을 받는 클라이언트 목록 (쉼표 구분)")
    parser.add_argument("--fail-on-breaking", action="store_true", help="breaking finding 이 있으면 exit 1")
    return parser.parse_args()


def load_spec(path: str) -> dict:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        if yaml is None:
            sys.exit("YAML 스펙을 읽으려면 PyYAML이 필요합니다. 스킬의 도구 설치 원칙에 따라 설치하세요.")
        data = yaml.safe_load(text)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if yaml is None:
                sys.exit("JSON/YAML 파서가 필요합니다. 스킬의 도구 설치 원칙에 따라 PyYAML을 설치하세요.")
            data = yaml.safe_load(text)
    if not isinstance(data, dict):
        sys.exit(f"OpenAPI 스펙이 객체가 아닙니다: {path}")
    if not str(data.get("openapi", "")).startswith("3."):
        print(f"warning: OpenAPI 3.x가 아닐 수 있습니다: {path} (openapi={data.get('openapi')})", file=sys.stderr)
    return data


def resolve_pointer(root: dict, ref: str):
    current = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def resolve(node, root: dict, unresolved: set[str], seen: set[int] | None = None):
    if isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/"):
            unresolved.add(str(ref))
            return node
        target = resolve_pointer(root, ref)
        if target is None:
            unresolved.add(ref)
            return node
        if seen is None:
            seen = set()
        if id(target) in seen:
            return {}
        return resolve(target, root, unresolved, seen | {id(target)})
    if isinstance(node, dict):
        return {key: resolve(value, root, unresolved, seen) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve(value, root, unresolved, seen) for value in node]
    return node


def compact(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = text.replace("|", "\\|")
    return text[:220] + ("…" if len(text) > 220 else "")


def add(findings, severity, area, location, message, old=None, new=None, action=""):
    findings.append(
        {
            "severity": severity,
            "area": area,
            "location": location,
            "message": message,
            "old": compact(old),
            "new": compact(new),
            "action": action,
        }
    )



def schema_shape(schema, root: dict, unresolved: set[str]) -> str:
    schema = resolve(schema, root, unresolved)
    if not isinstance(schema, dict):
        return "-"
    typ = schema.get("type")
    if isinstance(typ, list):
        typ = "|".join(str(x) for x in typ)
    elif typ is None and "properties" in schema:
        typ = "object"
    elif typ is None and "items" in schema:
        typ = "array"
    parts = []
    if typ:
        parts.append(str(typ))
    props = schema.get("properties") or {}
    if isinstance(props, dict) and props:
        names = sorted(props)
        parts.append("fields=" + ",".join(names[:12]) + ("…" if len(names) > 12 else ""))
    required = schema.get("required") or []
    if required:
        parts.append("required=" + ",".join(sorted(str(x) for x in required)[:12]))
    enum = schema.get("enum")
    if enum:
        parts.append("enum=" + ",".join(str(x) for x in enum[:12]))
    items = schema.get("items")
    if isinstance(items, dict):
        parts.append("items=" + schema_shape(items, root, unresolved))
    return "; ".join(parts) or "-"


def content_example(content, media: str) -> str:
    if not isinstance(content, dict):
        return ""
    item = content.get(media) or {}
    if "example" in item:
        return json.dumps(item["example"], ensure_ascii=False, sort_keys=True)
    examples = item.get("examples") or {}
    if isinstance(examples, dict):
        values = {
            key: value.get("value")
            for key, value in examples.items()
            if isinstance(value, dict) and "value" in value
        }
        if values:
            return json.dumps(values, ensure_ascii=False, sort_keys=True)
    return ""


def add_body_change(body_changes, operation, direction, status, media, change, old_schema, new_schema, old_content, new_content, old_root, new_root, unresolved):
    old_shape = schema_shape(old_schema, old_root, unresolved)
    new_shape = schema_shape(new_schema, new_root, unresolved)
    old_example = content_example(old_content, media)
    new_example = content_example(new_content, media)
    if change == "changed" and old_shape == new_shape and old_example == new_example:
        return
    body_changes.append(
        {
            "operation": operation,
            "direction": direction,
            "status": status,
            "media_type": media,
            "change": change,
            "old_shape": old_shape,
            "new_shape": new_shape,
            "example_changed": old_example != new_example,
            "old_example": old_example,
            "new_example": new_example,
        }
    )

def compare_schema(old, new, location, direction, findings, old_root, new_root, unresolved):
    old = resolve(old, old_root, unresolved)
    new = resolve(new, new_root, unresolved)
    if not isinstance(old, dict) or not isinstance(new, dict):
        return

    if old.get("type") != new.get("type"):
        add(findings, "breaking", "SCHEMA", location, "타입이 변경됐습니다.", old.get("type"), new.get("type"), "이전 타입을 쓰는 클라이언트를 확인하고 버전 분리 또는 마이그레이션을 준비하세요.")
    if old.get("format") != new.get("format"):
        add(findings, "risky", "SCHEMA", location, "포맷이 변경됐습니다.", old.get("format"), new.get("format"), "클라이언트 파서와 유효성 검사를 확인하세요.")
    if old.get("nullable") != new.get("nullable"):
        add(findings, "risky", "SCHEMA", location, "nullable 이 변경됐습니다.", old.get("nullable"), new.get("nullable"), "null 허용 여부를 클라이언트와 확인하세요.")

    old_enum = old.get("enum")
    new_enum = new.get("enum")
    if isinstance(old_enum, list) and isinstance(new_enum, list):
        removed = [x for x in old_enum if x not in new_enum]
        added = [x for x in new_enum if x not in old_enum]
        if removed:
            add(findings, "breaking", "SCHEMA", location, "허용 값이 제거됐습니다.", removed, new_enum, "제거된 값을 보내는 클라이언트가 없는지 확인하세요.")
        if added:
            sev = "risky" if direction == "response" else "non-breaking"
            add(findings, sev, "SCHEMA", location, "허용 값이 추가됐습니다.", old_enum, added, "응답에 새 값이 나올 때 클라이언트가 처리할 수 있는지 확인하세요." if direction == "response" else "서버가 새 값을 허용하는지 확인하세요.")

    old_props = old.get("properties") or {}
    new_props = new.get("properties") or {}
    old_required = set(old.get("required") or [])
    new_required = set(new.get("required") or [])
    for name in sorted(new_required - old_required):
        sev = "breaking" if direction == "request" else "risky"
        action = "클라이언트가 값을 보내도록 배포 순서를 조정하세요." if direction == "request" else "응답을 엄격히 검증하는 클라이언트가 있는지 확인하세요."
        add(findings, sev, "SCHEMA", f"{location}.{name}", "필수 필드가 추가됐습니다.", "-", "required", action)
    for name in sorted(old_required - new_required):
        if name in old_props and name not in new_props:
            continue
        sev = "non-breaking" if direction == "request" else "breaking"
        add(findings, sev, "SCHEMA", f"{location}.{name}", "필수 조건이 제거됐습니다.", "required", "-", "응답이면 이전에 보장되던 필드가 빠질 수 있는지 확인하세요.")

    if isinstance(old_props, dict) and isinstance(new_props, dict):
        for name in sorted(set(old_props) - set(new_props)):
            sev = "risky" if direction == "request" else "breaking"
            action = "서버가 알 수 없는 필드를 무시하는지 확인하세요." if direction == "request" else "이 필드를 사용하는 클라이언트 화면과 로직을 확인하세요."
            add(findings, sev, "SCHEMA", f"{location}.{name}", "필드가 제거됐습니다.", name, "-", action)
        for name in sorted(set(new_props) - set(old_props)):
            if name in new_required:
                continue
            add(findings, "non-breaking", "SCHEMA", f"{location}.{name}", "필드가 추가됐습니다.", "-", name, "응답이면 클라이언트가 무시할 수 있는지 확인하세요.")
        for name in sorted(set(old_props) & set(new_props)):
            compare_schema(old_props[name], new_props[name], f"{location}.{name}", direction, findings, old_root, new_root, unresolved)

    old_items = old.get("items")
    new_items = new.get("items")
    if old_items is not None or new_items is not None:
        compare_schema(old_items, new_items, f"{location}[]", direction, findings, old_root, new_root, unresolved)

    for key in ("oneOf", "anyOf", "allOf"):
        if old.get(key) != new.get(key):
            add(findings, "risky", "SCHEMA", f"{location}.{key}", f"{key} 구성이 변경됐습니다.", old.get(key), new.get(key), "조합 스키마 변경은 클라이언트 역직렬화와 유효성 검사를 확인하세요.")

    for key in ("minimum", "maximum", "pattern", "minLength", "maxLength", "minItems", "maxItems"):
        if old.get(key) != new.get(key):
            add(findings, "risky", "SCHEMA", f"{location}.{key}", "제약 조건이 변경됐습니다.", old.get(key), new.get(key), "경계값 테스트를 추가하세요.")

    if old.get("additionalProperties") != new.get("additionalProperties"):
        add(findings, "risky", "SCHEMA", location, "additionalProperties 가 변경됐습니다.", old.get("additionalProperties"), new.get("additionalProperties"), "알 수 없는 필드 허용 정책을 확인하세요.")


def parameter_map(operation, path_item, root, unresolved):
    params = []
    for raw in (path_item or {}).get("parameters", []) or []:
        params.append(resolve(raw, root, unresolved))
    for raw in (operation or {}).get("parameters", []) or []:
        params.append(resolve(raw, root, unresolved))
    result = {}
    for param in params:
        if isinstance(param, dict) and "name" in param and "in" in param:
            result[(str(param["name"]), str(param["in"]))] = param
    return result


def compare_parameters(old_op, new_op, old_path_item, new_path_item, location, findings, old_root, new_root, unresolved):
    old_params = parameter_map(old_op, old_path_item, old_root, unresolved)
    new_params = parameter_map(new_op, new_path_item, new_root, unresolved)
    for key in sorted(set(old_params) - set(new_params)):
        name, where = key
        old_param = old_params[key]
        sev = "breaking" if old_param.get("required") else "risky"
        add(findings, sev, "PARAM", f"{location} {where}.{name}", "파라미터가 제거됐습니다.", name, "-", "클라이언트가 이 파라미터를 보내는지 확인하세요.")
    for key in sorted(set(new_params) - set(old_params)):
        name, where = key
        new_param = new_params[key]
        sev = "breaking" if new_param.get("required") else "non-breaking"
        add(findings, sev, "PARAM", f"{location} {where}.{name}", "파라미터가 추가됐습니다.", "-", name, "필수 파라미터라면 클라이언트 배포 순서를 조정하세요.")
    for key in sorted(set(old_params) & set(new_params)):
        name, where = key
        old_param = old_params[key]
        new_param = new_params[key]
        loc = f"{location} {where}.{name}"
        if bool(old_param.get("required")) != bool(new_param.get("required")):
            sev = "breaking" if new_param.get("required") else "non-breaking"
            add(findings, sev, "PARAM", loc, "필수 여부가 변경됐습니다.", old_param.get("required"), new_param.get("required"), "클라이언트가 값을 항상 보내는지 확인하세요.")
        if old_param.get("style") != new_param.get("style") or old_param.get("explode") != new_param.get("explode"):
            add(findings, "risky", "PARAM", loc, "직렬화 방식이 변경됐습니다.", {"style": old_param.get("style"), "explode": old_param.get("explode")}, {"style": new_param.get("style"), "explode": new_param.get("explode")}, "클라이언트의 쿼리 직렬화를 확인하세요.")
        compare_schema(old_param.get("schema"), new_param.get("schema"), f"{loc}.schema", "request", findings, old_root, new_root, unresolved)


def compare_request_body(old_op, new_op, location, findings, body_changes, old_root, new_root, unresolved):
    old_body = resolve(old_op.get("requestBody"), old_root, unresolved) if old_op else None
    new_body = resolve(new_op.get("requestBody"), new_root, unresolved) if new_op else None
    if old_body is None and new_body is None:
        return
    old_content = (old_body or {}).get("content") or {}
    new_content = (new_body or {}).get("content") or {}
    if old_body is None:
        sev = "breaking" if isinstance(new_body, dict) and new_body.get("required") else "non-breaking"
        add(findings, sev, "REQUEST", location, "요청 본문이 추가됐습니다.", "-", "requestBody", "새 본문을 보내야 하는 클라이언트를 확인하세요.")
        for media in sorted(new_content):
            add_body_change(body_changes, location, "request", "-", media, "added", None, (new_content[media] or {}).get("schema"), {}, new_content, old_root, new_root, unresolved)
        return
    if new_body is None:
        add(findings, "risky", "REQUEST", location, "요청 본문이 제거됐습니다.", "requestBody", "-", "서버가 기존 본문을 무시하는지 확인하세요.")
        for media in sorted(old_content):
            add_body_change(body_changes, location, "request", "-", media, "removed", (old_content[media] or {}).get("schema"), None, old_content, {}, old_root, new_root, unresolved)
        return
    if bool(old_body.get("required")) != bool(new_body.get("required")):
        sev = "breaking" if new_body.get("required") else "non-breaking"
        add(findings, sev, "REQUEST", location, "요청 본문 필수 여부가 변경됐습니다.", old_body.get("required"), new_body.get("required"), "클라이언트가 본문을 항상 보내는지 확인하세요.")
    if isinstance(old_content, dict) and isinstance(new_content, dict):
        for media in sorted(set(old_content) - set(new_content)):
            add(findings, "breaking", "REQUEST", f"{location} {media}", "요청 미디어 타입이 제거됐습니다.", media, "-", "해당 Content-Type을 쓰는 클라이언트를 확인하세요.")
            add_body_change(body_changes, location, "request", "-", media, "removed", (old_content[media] or {}).get("schema"), None, old_content, {}, old_root, new_root, unresolved)
        for media in sorted(set(new_content) - set(old_content)):
            add(findings, "non-breaking", "REQUEST", f"{location} {media}", "요청 미디어 타입이 추가됐습니다.", "-", media, "서버가 새 타입을 처리하는지 확인하세요.")
            add_body_change(body_changes, location, "request", "-", media, "added", None, (new_content[media] or {}).get("schema"), {}, new_content, old_root, new_root, unresolved)
        for media in sorted(set(old_content) & set(new_content)):
            old_schema = (old_content[media] or {}).get("schema")
            new_schema = (new_content[media] or {}).get("schema")
            compare_schema(old_schema, new_schema, f"{location} {media}", "request", findings, old_root, new_root, unresolved)
            add_body_change(body_changes, location, "request", "-", media, "changed", old_schema, new_schema, old_content, new_content, old_root, new_root, unresolved)


def compare_responses(old_op, new_op, location, findings, body_changes, old_root, new_root, unresolved):
    old_responses = resolve((old_op or {}).get("responses") or {}, old_root, unresolved)
    new_responses = resolve((new_op or {}).get("responses") or {}, new_root, unresolved)
    if not isinstance(old_responses, dict) or not isinstance(new_responses, dict):
        return
    for status in sorted(set(old_responses) - set(new_responses), key=str):
        add(findings, "breaking", "RESPONSE", f"{location} {status}", "응답 상태 코드가 제거됐습니다.", status, "-", "클라이언트가 이 상태를 처리하는지 확인하세요.")
        content = (old_responses[status] or {}).get("content") or {}
        for media in sorted(content):
            add_body_change(body_changes, location, "response", str(status), media, "removed", (content[media] or {}).get("schema"), None, content, {}, old_root, new_root, unresolved)
    for status in sorted(set(new_responses) - set(old_responses), key=str):
        add(findings, "non-breaking", "RESPONSE", f"{location} {status}", "응답 상태 코드가 추가됐습니다.", "-", status, "클라이언트가 새 상태를 처리할 수 있는지 확인하세요.")
        content = (new_responses[status] or {}).get("content") or {}
        for media in sorted(content):
            add_body_change(body_changes, location, "response", str(status), media, "added", None, (content[media] or {}).get("schema"), {}, content, old_root, new_root, unresolved)
    for status in sorted(set(old_responses) & set(new_responses), key=str):
        old_response = old_responses[status] or {}
        new_response = new_responses[status] or {}
        old_content = old_response.get("content") or {}
        new_content = new_response.get("content") or {}
        if isinstance(old_content, dict) and isinstance(new_content, dict):
            for media in sorted(set(old_content) - set(new_content)):
                add(findings, "breaking", "RESPONSE", f"{location} {status} {media}", "응답 미디어 타입이 제거됐습니다.", media, "-", "클라이언트 파서를 확인하세요.")
                add_body_change(body_changes, location, "response", str(status), media, "removed", (old_content[media] or {}).get("schema"), None, old_content, {}, old_root, new_root, unresolved)
            for media in sorted(set(new_content) - set(old_content)):
                add(findings, "non-breaking", "RESPONSE", f"{location} {status} {media}", "응답 미디어 타입이 추가됐습니다.", "-", media, "클라이언트가 새 타입을 처리할 수 있는지 확인하세요.")
                add_body_change(body_changes, location, "response", str(status), media, "added", None, (new_content[media] or {}).get("schema"), {}, new_content, old_root, new_root, unresolved)
            for media in sorted(set(old_content) & set(new_content)):
                old_schema = (old_content[media] or {}).get("schema")
                new_schema = (new_content[media] or {}).get("schema")
                compare_schema(old_schema, new_schema, f"{location} {status} {media}", "response", findings, old_root, new_root, unresolved)
                add_body_change(body_changes, location, "response", str(status), media, "changed", old_schema, new_schema, old_content, new_content, old_root, new_root, unresolved)


def compare_operation(old_op, new_op, old_path_item, new_path_item, location, findings, body_changes, old_root, new_root, unresolved):
    if not old_op or not new_op:
        return
    if bool(old_op.get("deprecated")) != bool(new_op.get("deprecated")):
        add(findings, "info", "OPERATION", location, "deprecated 표시가 변경됐습니다.", old_op.get("deprecated"), new_op.get("deprecated"), "클라이언트 공지와 제거 일정을 확인하세요.")
    old_id = old_op.get("operationId")
    new_id = new_op.get("operationId")
    if old_id != new_id:
        add(findings, "risky", "OPERATION", location, "operationId가 변경됐습니다.", old_id, new_id, "SDK를 생성하는 클라이언트가 있으면 메서드명이 바뀔 수 있습니다.")
    compare_parameters(old_op, new_op, old_path_item, new_path_item, location, findings, old_root, new_root, unresolved)
    compare_request_body(old_op, new_op, location, findings, body_changes, old_root, new_root, unresolved)
    compare_responses(old_op, new_op, location, findings, body_changes, old_root, new_root, unresolved)


def compare_specs(old: dict, new: dict) -> tuple[list[dict], list[dict], set[str]]:
    findings: list[dict] = []
    body_changes: list[dict] = []
    unresolved: set[str] = set()

    old_version = (old.get("info") or {}).get("version")
    new_version = (new.get("info") or {}).get("version")
    if old_version != new_version:
        add(findings, "info", "META", "info.version", "스펙 버전이 변경됐습니다.", old_version, new_version, "배포 버전과 클라이언트 공지를 확인하세요.")

    old_servers = old.get("servers") or []
    new_servers = new.get("servers") or []
    if old_servers != new_servers:
        add(findings, "risky", "SERVER", "servers", "서버 URL 또는 설명이 변경됐습니다.", old_servers, new_servers, "클라이언트의 base URL 설정을 확인하세요.")

    old_paths = old.get("paths") or {}
    new_paths = new.get("paths") or {}
    if isinstance(old_paths, dict) and isinstance(new_paths, dict):
        removed_paths = set(old_paths) - set(new_paths)
        if old_paths and not new_paths:
            add(findings, "breaking", "PATH", "PATH *", "모든 API 경로가 제거됐습니다.", "-", "-", "서비스 중단 여부를 즉시 확인하세요.")
        else:
            for path in sorted(removed_paths):
                add(findings, "breaking", "PATH", f"PATH {path}", "경로가 제거됐습니다.", path, "-", "해당 경로를 호출하는 클라이언트를 확인하세요.")
        for path in sorted(set(new_paths) - set(old_paths)):
            add(findings, "non-breaking", "PATH", f"PATH {path}", "경로가 추가됐습니다.", "-", path, "새 경로를 사용할 클라이언트를 확인하세요.")
        for path in sorted(set(old_paths) & set(new_paths)):
            old_item = old_paths[path] or {}
            new_item = new_paths[path] or {}
            for method in METHODS:
                old_op = old_item.get(method)
                new_op = new_item.get(method)
                loc = f"{method.upper()} {path}"
                if old_op and not new_op:
                    add(findings, "breaking", "OPERATION", loc, "오퍼레이션이 제거됐습니다.", method, "-", "해당 엔드포인트를 호출하는 클라이언트를 확인하세요.")
                elif new_op and not old_op:
                    add(findings, "non-breaking", "OPERATION", loc, "오퍼레이션이 추가됐습니다.", "-", method, "새 엔드포인트를 사용할 클라이언트를 확인하세요.")
                elif old_op and new_op:
                    compare_operation(old_op, new_op, old_item, new_item, loc, findings, body_changes, old_root=old, new_root=new, unresolved=unresolved)

    old_security = old.get("security") or []
    new_security = new.get("security") or []
    if old_security != new_security:
        if not old_security and new_security:
            add(findings, "breaking", "AUTH", "security", "전역 인증 요구가 추가됐습니다.", old_security, new_security, "클라이언트가 새 인증을 지원하는지 확인하세요.")
        elif old_security and not new_security:
            add(findings, "non-breaking", "AUTH", "security", "전역 인증 요구가 제거됐습니다.", old_security, new_security, "인증 제거가 의도된 변경인지 확인하세요.")
        else:
            add(findings, "breaking", "AUTH", "security", "전역 인증 방식이 변경됐습니다.", old_security, new_security, "토큰·헤더·스코프 변경을 클라이언트에 공지하세요.")

    old_schemes = ((old.get("components") or {}).get("securitySchemes") or {})
    new_schemes = ((new.get("components") or {}).get("securitySchemes") or {})
    if isinstance(old_schemes, dict) and isinstance(new_schemes, dict):
        for name in sorted(set(old_schemes) - set(new_schemes)):
            add(findings, "breaking", "AUTH", f"securitySchemes.{name}", "인증 스킴이 제거됐습니다.", name, "-", "이 스킴을 사용하는 오퍼레이션과 클라이언트를 확인하세요.")
        for name in sorted(set(new_schemes) - set(old_schemes)):
            add(findings, "non-breaking", "AUTH", f"securitySchemes.{name}", "인증 스킴이 추가됐습니다.", "-", name, "새 인증 스킴을 사용할 클라이언트를 확인하세요.")
        for name in sorted(set(old_schemes) & set(new_schemes)):
            if old_schemes[name] != new_schemes[name]:
                add(findings, "breaking", "AUTH", f"securitySchemes.{name}", "인증 스킴 정의가 변경됐습니다.", old_schemes[name], new_schemes[name], "토큰 형식·헤더·스코프 변경을 확인하세요.")

    if unresolved:
        for ref in sorted(unresolved):
            add(findings, "risky", "SPEC", "$ref", "외부 또는 해석할 수 없는 $ref가 있습니다.", ref, "-", "외부 스펙을 포함해 다시 비교하거나 수동 검토하세요.")

    counters = Counter()
    for finding in findings:
        severity = finding["severity"]
        counters[severity] += 1
        finding["id"] = f"{PREFIXES[severity]}-{counters[severity]:02d}"
        finding["priority"] = priority_of(finding)
    return findings, body_changes, unresolved


def pretty_json(text: str) -> str:
    if not text:
        return "없음"
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        return text


def human_leaf(leaf: str) -> str:
    if not leaf:
        return leaf
    bare = {
        "maxLength": "최대 길이",
        "minLength": "최소 길이",
        "minimum": "최소값",
        "maximum": "최대값",
        "pattern": "형식",
        "maxItems": "최대 항목 수",
        "minItems": "최소 항목 수",
        "exclusiveMinimum": "최소값(미포함)",
        "exclusiveMaximum": "최대값(미포함)",
        "multipleOf": "배수 조건",
    }
    if leaf in bare:
        return bare[leaf]
    suffixes = {
        ".maxLength": " 최대 길이",
        ".minLength": " 최소 길이",
        ".minimum": " 최소값",
        ".maximum": " 최대값",
        ".pattern": " 형식",
        ".maxItems": " 최대 항목 수",
        ".minItems": " 최소 항목 수",
        ".exclusiveMinimum": " 최소값(미포함)",
        ".exclusiveMaximum": " 최대값(미포함)",
        ".multipleOf": " 배수 조건",
    }
    for suffix, label in suffixes.items():
        if leaf.endswith(suffix):
            return leaf[: -len(suffix)] + label
    return leaf


def human_location(location: str) -> str:
    location = location.strip()
    if location == "security":
        return "인증"
    if location == "info.version":
        return "스펙 버전"
    if location == "servers":
        return "서버 URL"
    if location == "$ref":
        return "외부 참조"
    if location.startswith("securitySchemes."):
        return "인증 스킴 " + location.split(".", 1)[1]
    match = re.match(r"^(PATH|GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|TRACE) (\S+)(?: (.*))?$", location)
    if not match:
        return location
    method, path, tail = match.group(1), match.group(2), match.group(3) or ""
    if method == "PATH":
        return f"경로 {path}"
    base = f"{method} {path}"
    if not tail:
        return base
    for prefix, label in (("query.", "쿼리 파라미터"), ("path.", "경로 파라미터"), ("header.", "헤더"), ("cookie.", "쿠키")):
        if tail.startswith(prefix):
            return f"{base} → {label} {tail[len(prefix):]}"
    tokens = tail.split()
    status = None
    if tokens and (tokens[0].isdigit() or tokens[0].lower() in {"default", "2xx", "3xx", "4xx", "5xx"}):
        status = tokens.pop(0)
    if not tokens:
        return f"{base} → 응답 {status}" if status else base
    media = tokens.pop(0)
    leaf = ""
    if "." in media:
        media, leaf = media.split(".", 1)
    elif tokens:
        leaf = " ".join(tokens)
    body = "응답 본문" if status else "요청 본문"
    leaf = human_leaf(leaf)
    if leaf:
        return f"{base} → 응답 {status} 본문 → {leaf}" if status else f"{base} → {body} → {leaf}"
    return f"{base} → 응답 {status} 본문 ({media})" if status else f"{base} → {body} ({media})"


def display_value(value: str) -> str:
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return ", ".join(str(item) for item in parsed)
        if isinstance(parsed, str):
            return parsed
    except (TypeError, ValueError):
        pass
    return value


def inline(value: str) -> str:
    text = str(value).strip()
    if not text:
        return ""
    if text.startswith("`") and text.endswith("`"):
        return text
    return f"`{text}`"


def raw_field(location: str) -> str:
    loc = human_location(location)
    for marker in ("본문 → ", "쿼리 파라미터 ", "경로 파라미터 ", "헤더 ", "쿠키 "):
        if marker in loc:
            return loc.rsplit(marker, 1)[1]
    return loc


def format_field(field: str) -> str:
    for suffix in (" 최대 길이", " 최소 길이", " 최소값(미포함)", " 최대값(미포함)", " 최소값", " 최대값", " 최대 항목 수", " 최소 항목 수", " 배수 조건", " 형식"):
        if field.endswith(suffix):
            return inline(field[: -len(suffix)]) + suffix
    return inline(field)


def is_response(location: str) -> bool:
    return bool(
        re.match(
            r"^(?:PATH|GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|TRACE) \S+ (?:\d{3}|default|[1-5]xx)\b",
            location,
        )
    )


def priority_of(finding: dict) -> str:
    severity = finding["severity"]
    message = finding["message"]
    location = finding["location"]
    if severity == "info":
        return "P4"
    if severity == "non-breaking":
        return "P4"
    if severity == "risky":
        return "P3"
    if "모든 API 경로가 제거" in message:
        return "P0"
    if location == "security" or location.startswith("securitySchemes."):
        return "P1"
    if "서버 URL" in message or "경로가 제거" in message or "오퍼레이션이 제거" in message:
        return "P1"
    if "요청 본문" in message or "요청 미디어 타입" in message or "파라미터가 추가" in message:
        return "P1"
    if "필수 필드가 추가" in message:
        return "P2" if is_response(location) else "P1"
    if "필수 여부가 변경" in message:
        return "P1" if finding["new"] == "True" else "P4"
    if "필드가 제거" in message or "허용 값이 제거" in message or "타입이 변경" in message:
        return "P2" if is_response(location) else "P1"
    if "파라미터가 제거" in message:
        return "P2" if is_response(location) else "P1"
    if "응답 상태 코드가 제거" in message or "응답 미디어 타입이 제거" in message:
        return "P2"
    return "P2"


def priority_rank(priority: str) -> int:
    return PRIORITIES.index(priority) if priority in PRIORITIES else len(PRIORITIES)


def group_priority(findings: list[dict]) -> str:
    if not findings:
        return "P4"
    return min((priority_of(finding) for finding in findings), key=priority_rank)


def sentence_change(finding: dict) -> tuple[str, str]:
    message = finding["message"]
    old = finding["old"]
    new = finding["new"]
    location = finding["location"]
    field = raw_field(location)
    ff = format_field(field)
    response = is_response(location)
    direction = "응답" if response else "요청"
    if "모든 API 경로가 제거" in message:
        return "모든 API 경로가 제거됩니다.", "모든 클라이언트 호출이 실패할 수 있습니다."
    if "필드가 제거" in message:
        impact = "이 값을 표시하던 화면은 빈칸이 되거나 오류가 날 수 있습니다." if response else "이 필드를 보내던 클라이언트는 값이 무시되거나 요청이 실패할 수 있습니다."
        return f"{direction}에서 {ff} 필드가 제거됩니다.", impact
    if "필수 필드가 추가" in message:
        if response:
            return f"응답에 {ff} 필드가 항상 포함됩니다.", "이 필드를 필수로 가정하지 않는 클라이언트는 영향이 없습니다."
        return f"요청에 {ff} 필드가 필수가 됩니다.", "이 값을 보내지 않으면 요청이 실패합니다."
    if "필수 조건이 제거" in message:
        if response:
            return f"응답에서 {ff}가 항상 포함되지 않을 수 있습니다.", "이 값을 필수로 가정한 화면은 빈칸이 될 수 있습니다."
        return f"요청에서 {ff}가 필수에서 빠집니다.", "값을 보내지 않아도 됩니다. 기존 클라이언트는 영향이 없습니다."
    if "필드가 추가" in message:
        if response:
            return f"응답에 {ff} 필드가 추가됩니다.", "새 필드가 추가됩니다. 기존 클라이언트는 무시하면 됩니다."
        return f"요청에 {ff} 필드를 보낼 수 있습니다.", "기존 클라이언트는 영향이 없습니다."
    if "허용 값이 제거" in message:
        if response:
            return f"{ff}에서 {inline(display_value(old))} 값이 제거됩니다.", "이 값을 처리하던 화면은 오류가 날 수 있습니다."
        return f"{ff}에서 {inline(display_value(old))} 값을 보낼 수 없습니다.", "이 값을 보내던 클라이언트는 요청이 실패할 수 있습니다."
    if "허용 값이 추가" in message:
        if response:
            return f"{ff}에 {inline(display_value(new))} 값이 추가됩니다.", "새 값을 모르는 클라이언트는 오류가 날 수 있습니다."
        return f"{ff}에 {inline(display_value(new))} 값을 보낼 수 있습니다.", "기존 클라이언트는 영향이 없습니다."
    if "필수 여부가 변경" in message:
        if new == "True":
            return f"{ff} 파라미터가 필수가 됩니다.", "이 파라미터 없이 호출하면 실패합니다."
        return f"{ff} 파라미터가 선택으로 바뀝니다.", "값을 보내지 않아도 됩니다."
    if "타입이 변경" in message:
        return f"{ff} 타입이 {inline(old)}에서 {inline(new)}로 바뀝니다.", "이전 타입 값을 보내거나 읽으면 오류가 날 수 있습니다."
    if "제약 조건이 변경" in message:
        impact = "경계값에서 기존과 다르게 동작할 수 있습니다."
        try:
            if str(old).isdigit() and str(new).isdigit():
                unit = "자" if "길이" in field else "개" if "항목" in field else ""
                if int(new) < int(old):
                    change = f"{ff}가 {old}{unit}에서 {new}{unit}로 줄어듭니다."
                    impact = f"{new}{unit}를 넘는 값은 거부되거나 잘릴 수 있습니다."
                elif int(new) > int(old):
                    change = f"{ff}가 {old}{unit}에서 {new}{unit}로 늘어납니다."
                else:
                    change = f"{ff}가 {old}{unit}에서 {new}{unit}로 바뀝니다."
                return change, impact
        except (TypeError, ValueError):
            pass
        return f"{ff}가 {old}에서 {new}로 바뀝니다.", impact
    if "포맷이 변경" in message:
        return f"{ff} 형식이 {inline(old)}에서 {inline(new)}로 바뀝니다.", "이전 형식으로 보내거나 읽던 클라이언트는 오류가 날 수 있습니다."
    if "nullable" in message:
        return f"{ff}의 null 허용 여부가 바뀝니다.", "null을 보내거나 받는 클라이언트는 동작이 달라질 수 있습니다."
    if "additionalProperties" in message:
        return f"{ff}의 알 수 없는 필드 허용 정책이 바뀝니다.", "알 수 없는 필드를 보내거나 받는 클라이언트는 오류가 날 수 있습니다."
    if "응답 상태 코드가 제거" in message:
        return f"{inline(old)} 응답이 사라집니다.", "이 상태를 따로 처리하던 클라이언트는 동작이 달라집니다."
    if "응답 상태 코드가 추가" in message:
        return f"{inline(new)} 응답이 추가됩니다.", "이 상태를 처리하지 않는 클라이언트는 예외가 날 수 있습니다."
    if "전역 인증 요구가 추가" in message:
        return "모든 API 호출에 인증이 필요해집니다.", "토큰 없이 호출하던 클라이언트는 401을 받습니다."
    if "전역 인증 요구가 제거" in message:
        return "전역 인증 요구가 사라집니다.", "기존 인증 코드는 그대로 동작할 수 있습니다."
    if "전역 인증 방식이 변경" in message:
        return "인증 방식이 바뀝니다.", "토큰·헤더·스코프가 바뀌면 기존 인증 코드가 실패할 수 있습니다."
    if "operationId" in message:
        return f"SDK 메서드명이 {inline(old)}에서 {inline(new)}로 바뀝니다.", "SDK를 다시 생성하면 기존 호출 코드가 컴파일 오류를 낼 수 있습니다."
    if "요청 본문이 추가" in message:
        return "요청 body가 새로 필요해집니다.", "본문 없이 호출하던 클라이언트는 실패할 수 있습니다."
    if "요청 본문이 제거" in message:
        return "요청 body가 더 이상 필요하지 않습니다.", "본문을 보내던 클라이언트는 값이 무시되거나 오류가 날 수 있습니다."
    if "요청 본문 필수 여부" in message:
        return "요청 body의 필수 여부가 바뀝니다.", "본문을 보내지 않던 클라이언트는 요청이 실패할 수 있습니다."
    if "요청 미디어 타입이 제거" in message:
        return f"{inline(old)} 요청 형식이 제거됩니다.", f"{inline(old)} 형식으로 요청하던 클라이언트는 실패할 수 있습니다."
    if "요청 미디어 타입이 추가" in message:
        return f"{inline(new)} 요청 형식이 추가됩니다.", "기존 요청 형식은 그대로 사용할 수 있습니다."
    if "응답 미디어 타입이 제거" in message:
        return f"{inline(old)} 응답 형식이 제거됩니다.", f"{inline(old)} 형식으로 응답을 받던 클라이언트는 실패할 수 있습니다."
    if "응답 미디어 타입이 추가" in message:
        return f"{inline(new)} 응답 형식이 추가됩니다.", "새 응답 형식을 처리하지 못하는 클라이언트는 오류가 날 수 있습니다."
    if "파라미터가 제거" in message:
        return f"{ff} 파라미터가 제거됩니다.", "이 파라미터를 보내던 클라이언트는 값이 무시되거나 오류가 날 수 있습니다."
    if "파라미터가 추가" in message:
        impact = "이 파라미터를 보내지 않으면 요청이 실패합니다." if finding["severity"] == "breaking" else "선택 파라미터라 기존 클라이언트 호출은 그대로 동작합니다."
        return f"{ff} 파라미터가 추가됩니다.", impact
    if "직렬화 방식이 변경" in message:
        return f"{ff}의 직렬화 방식이 바뀝니다.", "쿼리 직렬화가 바뀌면 기존 요청이 다르게 해석될 수 있습니다."
    if "경로가 추가" in message:
        return f"{inline(new)} 경로가 추가됩니다.", "기존 API 동작은 바뀌지 않습니다."
    if "경로가 제거" in message:
        return f"{inline(old)} 경로가 제거됩니다.", "이 API를 호출하던 클라이언트는 404를 받습니다."
    if "오퍼레이션이 추가" in message:
        return f"{inline(new)} API가 추가됩니다.", "기존 API 동작은 바뀌지 않습니다."
    if "오퍼레이션이 제거" in message:
        return f"{inline(old)} API가 제거됩니다.", "이 API를 호출하던 클라이언트는 404를 받습니다."
    if "deprecated" in message:
        return "지원 중단 표시가 변경됩니다.", "지원 중단 일정과 제거 버전을 확인해야 합니다."
    if "스펙 버전" in message:
        return f"스펙 버전이 {old}에서 {with_ro(new)} 바뀝니다.", "문서 버전만 바뀌었고 API 동작 변화는 아닙니다."
    if "서버 URL" in message:
        return "서버 URL이 변경됩니다.", "클라이언트의 base URL 설정이 바뀌지 않으면 다른 서버로 호출할 수 있습니다."
    if "$ref" in message:
        return "해석하지 못한 외부 참조가 있습니다.", "외부 스펙을 포함하지 않으면 이 부분은 비교되지 않았습니다."
    if "oneOf" in message or "anyOf" in message or "allOf" in message:
        return "조합 스키마가 변경됩니다.", "클라이언트 역직렬화와 유효성 검사가 실패할 수 있습니다."
    return message, "실제 클라이언트 사용처에서 영향을 확인해야 합니다."


def human_change(finding: dict) -> str:
    return sentence_change(finding)[0]


def human_impact(finding: dict) -> str:
    return sentence_change(finding)[1]


def change_scope(finding: dict) -> str:
    location = finding["location"]
    message = finding["message"]
    if "operationId" in message:
        return "SDK"
    if location == "security" or location.startswith("securitySchemes."):
        return "인증"
    if location.startswith("info."):
        return "문서"
    if location.startswith("servers"):
        return "공통"
    if location.startswith("PATH "):
        return "API"
    match = re.match(r"^(?:PATH|GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|TRACE) \S+ (\d{3}|default|[1-5]xx)\b", location)
    if match:
        return f"응답 {match.group(1)}"
    parts = location.split()
    if len(parts) >= 3:
        return "요청"
    if "요청" in message:
        return "요청"
    if "응답" in message:
        return "응답"
    return "API"


def joined(values: list[str], limit: int = 3) -> str:
    unique = list(dict.fromkeys(values))
    if len(unique) <= limit:
        return ", ".join(unique)
    return ", ".join(unique[:limit]) + f" 외 {len(unique) - limit}곳"


def grouped(findings: list[dict]) -> list[dict]:
    groups: dict[tuple, dict] = {}
    for finding in findings:
        key = (
            finding["severity"],
            priority_of(finding),
            finding["message"],
            finding["old"],
            finding["new"],
            finding["action"],
        )
        group = groups.setdefault(
            key,
            {"finding": finding, "ids": [], "locations": [], "findings": []},
        )
        group["ids"].append(finding["id"])
        group["locations"].append(finding["location"])
        group["findings"].append(finding)
    return list(groups.values())


def operation_of(finding: dict) -> str:
    match = re.match(r"^(PATH|GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|TRACE) (\S+)", finding["location"])
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return "공통"


def operation_sort(operation: str):
    if operation == "PATH *":
        return ("", 0)
    if operation.startswith("PATH "):
        return (operation[5:], 99)
    method, path = operation.split(" ", 1)
    order = {"GET": 1, "POST": 2, "PUT": 3, "PATCH": 4, "DELETE": 5}
    return (path, order.get(method, 50))


def operation_title(operation: str) -> str:
    if operation == "PATH *":
        return "전체 API"
    if operation.startswith("PATH "):
        return "새 경로 " + operation[5:]
    return operation


def endpoint_status(findings: list[dict]) -> str:
    priority = group_priority(findings)
    return f"{priority} · {PRIORITY_LABELS[priority]}"


def strip_direction(text: str) -> str:
    for prefix in ("요청에서 ", "응답에서 ", "요청에 ", "응답에 "):
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


def with_ro(value: str, particle: str = "로") -> str:
    if value and value[-1].isdigit() and int(value[-1]) in {0, 3, 6}:
        return value + "으로"
    return value + particle


def finding_bullet(finding: dict) -> str:
    label = priority_of(finding)
    scope = change_scope(finding)
    change = strip_direction(human_change(finding)).rstrip(".")
    impact = human_impact(finding)
    return f"- **{label} · {scope}** {change}. {impact}"


def first_check_priority(group: dict):
    finding = group["finding"]
    message = finding["message"]
    if finding["location"] == "security":
        return (0, 0)
    if "필수 필드가 추가" in message:
        return (1, 0)
    if "필드가 제거" in message:
        return (2, -len(group["locations"]))
    if "허용 값이 제거" in message:
        return (3, -len(group["locations"]))
    if "필수 여부가 변경" in message:
        return (4, 0)
    if "응답 상태 코드가 제거" in message:
        return (5, 0)
    return (6, 0)


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def json_diff(old_text: str, new_text: str) -> str:
    if not old_text:
        return "\n".join("+" + line for line in pretty_json(new_text).splitlines())
    if not new_text:
        return "\n".join("-" + line for line in pretty_json(old_text).splitlines())
    old = pretty_json(old_text)
    new = pretty_json(new_text)
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=1000)
    return "\n".join(line for line in diff if not line.startswith(("--- ", "+++ ", "@@ ")))


def markdown_report(old_path, new_path, old, new, findings, body_changes, clients, service, release_version):
    counts = Counter(f["severity"] for f in findings)
    breaking_groups = sorted(
        grouped([f for f in findings if f["severity"] == "breaking"]),
        key=lambda group: (priority_rank(group_priority(group["findings"])), first_check_priority(group)),
    )
    operation_findings: dict[str, list[dict]] = {}
    operation_bodies: dict[str, list[dict]] = {}
    for finding in findings:
        operation_findings.setdefault(operation_of(finding), []).append(finding)
    for body in body_changes:
        operation_bodies.setdefault(body["operation"], []).append(body)

    operations = sorted(
        (op for op in set(operation_findings) | set(operation_bodies) if op != "공통"),
        key=operation_sort,
    )
    common_findings = operation_findings.get("공통", [])

    priority_counts = Counter(priority_of(finding) for finding in findings)
    if priority_counts.get("P0", 0):
        conclusion = f"**P0 {priority_counts['P0']}건 · 전면 중단 위험** — 전체 API 또는 핵심 기능이 멈출 수 있는 변경이 있습니다."
    elif priority_counts.get("P1", 0):
        conclusion = f"**P1 {priority_counts['P1']}건 · 배포 전 수정 필요** — P2 {priority_counts.get('P2', 0)}건을 포함해 기존 클라이언트가 깨질 수 있는 변경이 {counts.get('breaking', 0)}건 있습니다."
    elif priority_counts.get("P2", 0):
        conclusion = f"**P2 {priority_counts['P2']}건 · 배포 전 확인 필요** — 응답 소비나 배포 순서를 확인해야 하는 변경이 있습니다."
    elif priority_counts.get("P3", 0):
        conclusion = f"**P3 {priority_counts['P3']}건 · 호환성 확인 필요** — 클라이언트 구현에 따라 영향이 있을 수 있는 변경이 있습니다."
    elif findings:
        conclusion = "**P4 · 참고** — 기존 클라이언트에 영향을 주는 변경은 없습니다."
    else:
        conclusion = "**변경 없음** — 두 스펙에서 계약 변경을 찾지 못했습니다."

    lines = [
        "# API 계약 변경 리포트",
        "",
        conclusion,
        "",
        f"- 서비스: {service or '-'}",
        f"- 비교: `{old_path}` (v{(old.get('info') or {}).get('version', '-')}) → `{new_path}` (v{(new.get('info') or {}).get('version', '-')})",
        f"- 배포 버전: {release_version or '-'}",
        f"- 영향 클라이언트: {clients or '입력 없음'}",
        f"- 생성 시각: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- 우선순위: P0 전면 중단 · P1 배포 전 수정 · P2 배포 전 확인 · P3 호환성 확인 · P4 참고",
        f"- 집계: P0 {priority_counts.get('P0', 0)} · P1 {priority_counts.get('P1', 0)} · P2 {priority_counts.get('P2', 0)} · P3 {priority_counts.get('P3', 0)} · P4 {priority_counts.get('P4', 0)}",
        "",
        "## 먼저 확인할 것",
        "",
    ]
    if breaking_groups:
        for index, group in enumerate(breaking_groups, start=1):
            finding = min(group["findings"], key=lambda item: priority_rank(priority_of(item)))
            priority = group_priority(group["findings"])
            change = human_change(finding).rstrip(".")
            impact = human_impact(finding)
            apis = [operation_of(item) for item in group["findings"]]
            apis = list(dict.fromkeys(api for api in apis if api != "공통"))
            suffix = f" — {joined(apis)}" if apis else ""
            lines.append(f"{index}. **[{priority}]** **{change}.** {impact}{suffix}")
    elif counts.get("risky", 0):
        lines.append("- 배포를 막는 변경은 없습니다. 아래 ‘API별 변경’에서 확인이 필요한 항목을 보세요.")
    else:
        lines.append("- 기존 클라이언트에 영향을 주는 변경이 없습니다.")

    lines += ["", "## API별 변경", ""]
    if not operations:
        lines += ["- 변경된 엔드포인트가 없습니다.", ""]
    for operation in operations:
        group = operation_findings.get(operation, [])
        bodies = operation_bodies.get(operation, [])
        lines += [f"### {operation_title(operation)} — {endpoint_status(group)}", ""]
        if group:
            ordered = sorted(group, key=lambda finding: SEVERITIES.index(finding["severity"]))
            for finding in ordered:
                lines.append(finding_bullet(finding))
        else:
            lines.append("- 요청·응답 본문 구조가 변경됩니다. 실제 응답을 확인하세요.")
        lines.append("")

        for body in bodies:
            if not body["example_changed"]:
                continue
            direction = "요청" if body["direction"] == "request" else "응답"
            status = f" {body['status']}" if body["status"] != "-" else ""
            lines += [
                f"**{direction}{status} 예시 (이전 → 이후)**",
                "",
                "`-` 이전 값, `+` 이후 값",
                "",
                "```diff",
                json_diff(body["old_example"], body["new_example"]),
                "```",
                "",
            ]

    if common_findings:
        lines += ["## 공통 변경", ""]
        for finding in sorted(common_findings, key=lambda finding: SEVERITIES.index(finding["severity"])):
            lines.append(finding_bullet(finding))
        lines.append("")

    if findings:
        lines += ["## 배포 전 체크리스트", ""]
        if priority_counts.get("P0", 0):
            lines.append(f"- [ ] P0 변경 {priority_counts['P0']}건은 서비스 중단 여부를 즉시 확인")
        if priority_counts.get("P1", 0):
            lines.append(f"- [ ] P1 변경 {priority_counts['P1']}건은 배포 전에 수정하거나 배포 순서를 조정")
        if priority_counts.get("P2", 0):
            lines.append(f"- [ ] P2 변경 {priority_counts['P2']}건은 실제 클라이언트 사용처와 대조")
        if priority_counts.get("P3", 0):
            lines.append(f"- [ ] P3 변경 {priority_counts['P3']}건은 파서·SDK·게이트웨이 정책과 함께 확인")
        if not any(priority_counts.get(priority, 0) for priority in ("P0", "P1", "P2", "P3")):
            lines.append("- [ ] 기존 계약 테스트와 실제 응답 샘플 확인")
        lines += [
            "- [ ] 서버와 클라이언트 배포 순서 결정 (서버 먼저 / 클라이언트 먼저 / API 버전 분리)",
            "- [ ] 제거된 필드·enum 값·상태 코드를 사용하는 코드와 화면 검색",
            "- [ ] 인증 없이 호출하는 경로와 토큰 갱신 흐름 확인",
        ]
        lines += ["", "## 테스트 체크리스트", ""]
        lines += [
            "- [ ] 변경된 API의 정상·실패 응답 확인",
            "- [ ] 요청 필수값을 빼고 호출했을 때 오류 확인",
            "- [ ] 응답에서 빠진 필드·새 enum 값·새 상태 코드 처리 확인",
            "- [ ] 토큰 없이 호출했을 때 401 확인",
            "",
        ]
    else:
        lines += ["## 다음 단계", "", "- 배포 전 확인할 계약 변경이 없습니다. 기존 계약 테스트만 실행하세요.", ""]

    lines += ["## 확인이 필요한 것", ""]
    unresolved = [f for f in findings if f["area"] == "SPEC"]
    if unresolved:
        for finding in unresolved:
            lines.append(f"- {human_location(finding['location'])} — 외부 스펙 포함 여부 확인")
    else:
        lines.append("- 스펙에 없는 게이트웨이 정책, 실제 응답, 클라이언트 구현은 별도 확인")
    lines += [
        "",
        "> 이 리포트는 스펙 비교 결과입니다. 런타임 동작과 실제 클라이언트 영향은 별도 검증이 필요합니다.",
        "",
        "## 부록: 전체 변경 목록",
        "",
    ]
    if findings:
        lines += ["| ID | 우선순위 | 위치 | 변경 |", "| --- | --- | --- | --- |"]
        for finding in sorted(findings, key=lambda item: (priority_rank(priority_of(item)), item["id"])):
            label = priority_of(finding)
            location = human_location(finding["location"])
            change = strip_direction(human_change(finding))
            lines.append(f"| {finding['id']} | {cell(label)} | {cell(location)} | {cell(change)} |")
    else:
        lines.append("- 변경 없음")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    old = load_spec(args.old)
    new = load_spec(args.new)
    findings, body_changes, unresolved = compare_specs(old, new)
    report = markdown_report(args.old, args.new, old, new, findings, body_changes, args.clients, args.service, args.release_version)

    if args.out == "-":
        print(report)
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(str(out))

    if args.json_out:
        payload = {
            "old": args.old,
            "new": args.new,
            "service": args.service,
            "release_version": args.release_version,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "summary": dict(Counter(f["severity"] for f in findings)),
            "priority_summary": {priority: sum(1 for f in findings if f["priority"] == priority) for priority in PRIORITIES},
            "findings": findings,
            "body_changes": body_changes,
            "unresolved_refs": sorted(unresolved),
        }
        json_out = Path(args.json_out)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.fail_on_breaking and any(f["severity"] == "breaking" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
