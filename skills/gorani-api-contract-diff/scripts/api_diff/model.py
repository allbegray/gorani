"""비교 결과를 Markdown·JSON 렌더러가 소비하는 리포트 모델로 만든다."""

from collections import Counter

from .constants import PRIORITIES


def build_report_model(
    old_path,
    new_path,
    old,
    new,
    findings,
    body_changes,
    unresolved,
    service,
    release_version,
    clients,
    generated_at,
):
    return {
        "schema_version": 1,
        "old": old_path,
        "new": new_path,
        "old_version": (old.get("info") or {}).get("version", "-"),
        "new_version": (new.get("info") or {}).get("version", "-"),
        "service": service,
        "release_version": release_version,
        "clients": clients,
        "generated_at": generated_at,
        "summary": dict(Counter(finding["severity"] for finding in findings)),
        "priority_summary": {
            priority: sum(1 for finding in findings if finding["priority"] == priority)
            for priority in PRIORITIES
        },
        "findings": findings,
        "body_changes": body_changes,
        "unresolved_refs": sorted(unresolved),
    }
