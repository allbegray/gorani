"""리포트 모델 생성. JSON 직렬화 가능한 dict만 만든다."""

import re

from .constants import AREA_TEXT, KIND_TEXT, SCHEMA_VERSION


def build_title(summary, skill):
    title = re.sub(r"\s+", " ", summary).strip()
    if len(title) > 180:
        title = title[:177].rstrip() + "..."
    return f"[{skill}] {title}"


def build_report_model(result, values, environment):
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "repo": result["repo"],
            "skill": result["skill"],
            "skill_version": result["skill_version"],
            "skill_updated": result["skill_updated"],
            "kind": result["kind"],
            "kind_text": KIND_TEXT.get(result["kind"], result["kind"]),
            "area": result["area"],
            "area_text": AREA_TEXT.get(result["area"], result["area"]),
            "title": result["title"],
            "label": result["label"],
            "draft": result["draft"],
        },
        "summary": {
            "redactions": sum(result["redactions"].values()),
            "redaction_rules": len(result["redactions"]),
            "risks": len(result["risks"]),
            "duplicates": len(result["duplicates"]),
            "authenticated": result["authenticated"],
            "created": result["created"],
            "commented": result["commented"],
        },
        "values": values,
        "environment": environment,
        "body": result["body"],
        "duplicates": result["duplicates"],
        "duplicate_error": result["duplicate_error"],
        "redactions": result["redactions"],
        "risks": result["risks"],
        "authenticated": result["authenticated"],
        "auth_error": result["auth_error"],
        "created": result["created"],
        "commented": result["commented"],
        "url": result["url"],
        "error": result["error"],
    }
