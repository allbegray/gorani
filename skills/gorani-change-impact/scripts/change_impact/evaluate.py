"""manifest별 stale·clean·unknown 판정."""

from .git import changed_files, is_ancestor, last_manifest_commit, resolve_commit
from .manifest import filter_changed, match_sources


def evaluate(manifest, root, args, head_commit, working):
    errors = []
    if manifest.get("error"):
        errors.append(manifest["error"])
    generated = resolve_commit(root, manifest["generated_commit"])
    fallback = resolve_commit(root, args.base) if args.base.strip() else ""
    committed = ""
    base_commit = generated or fallback
    if not base_commit:
        committed = resolve_commit(root, last_manifest_commit(root, manifest["relative"]))
        base_commit = committed
    if not base_commit:
        if manifest["generated_commit"]:
            errors.append(f"기준 commit을 찾지 못했습니다: {manifest['generated_commit']}")
        else:
            errors.append("generated_commit 없음")
        return {
            "manifest": manifest,
            "status": "unknown",
            "base": "",
            "matched": [],
            "changed": 0,
            "errors": errors,
        }
    if not manifest["sources"]:
        return {
            "manifest": manifest,
            "status": "unknown",
            "base": base_commit,
            "matched": [],
            "changed": 0,
            "errors": errors,
        }
    files, error = changed_files(root, base_commit, head_commit)
    if files is None:
        errors.append(error)
        return {
            "manifest": manifest,
            "status": "unknown",
            "base": base_commit,
            "matched": [],
            "changed": 0,
            "errors": errors,
        }
    if working:
        files = sorted(set(files) | set(working))
    files = filter_changed(files, manifest)
    matched = sorted(item for item in files if match_sources(item, manifest["sources"]))
    if matched:
        if not committed:
            committed = resolve_commit(root, last_manifest_commit(root, manifest["relative"]))
        if committed and committed != base_commit and is_ancestor(root, base_commit, committed):
            newer_files, newer_error = changed_files(root, committed, head_commit)
            if newer_files is not None:
                if working:
                    newer_files = sorted(set(newer_files) | set(working))
                newer_files = filter_changed(newer_files, manifest)
                matched = sorted(item for item in newer_files if match_sources(item, manifest["sources"]))
                files = newer_files
                base_commit = committed
            else:
                errors.append(newer_error)
    return {
        "manifest": manifest,
        "status": "stale" if matched else "clean",
        "base": base_commit,
        "matched": matched,
        "changed": len(files),
        "errors": errors,
    }
