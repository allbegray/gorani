"""Markdown·JSON 렌더러가 함께 소비하는 리포트 모델을 만든다."""

from datetime import datetime


def now_iso(value):
    if value:
        return value
    return datetime.now().astimezone().isoformat(timespec="seconds")


def build_result(args, root, head_commit, stale, clean, unknown, categories, warnings):
    # schema_version은 리포트 모델 버전, version은 기존 JSON 소비자를 위한 결과 형식 버전이다.
    return {
        "schema_version": 1,
        "version": 1,
        "mode": args.mode,
        "generated_at": now_iso(args.now),
        "base": args.base if args.mode == "full" and args.base else "각 manifest의 최신 기준 commit",
        "head": head_commit,
        "manifest_glob": args.manifest_glob,
        "working": bool(args.working),
        "summary": {
            "changed_files": categories.get("_changed", 0),
            "stale": len(stale),
            "clean": len(clean),
            "unknown": len(unknown),
            "warnings": len(warnings),
        },
        "categories": {key: value for key, value in categories.items() if key != "_changed"},
        "stale": [
            {
                "manifest": item["manifest"]["relative"],
                "skill": item["manifest"]["skill"],
                "artifact": item["manifest"]["artifact"],
                "base": item["base"],
                "matched": item["matched"],
                "regenerate": item["manifest"]["regenerate"],
            }
            for item in stale
        ],
        "clean": [
            {
                "manifest": item["manifest"]["relative"],
                "skill": item["manifest"]["skill"],
                "artifact": item["manifest"]["artifact"],
            }
            for item in clean
        ],
        "unknown": [
            {
                "manifest": item["manifest"]["relative"],
                "skill": item["manifest"]["skill"],
                "artifact": item["manifest"]["artifact"],
                "errors": item["errors"],
            }
            for item in unknown
        ],
        "suggestions": [],
        "warnings": warnings,
    }
