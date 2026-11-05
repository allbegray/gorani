"""OpenAPI 스펙 로딩, $ref 해석, 계약 비교."""

import json
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from .constants import METHODS, PREFIXES
from .priority import priority_of

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
