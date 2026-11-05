"""sidecar .artifact.json manifest 생성."""

import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def repo_path(path):
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        return candidate.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def git_head_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def git_dirty():
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return bool(result.stdout.strip()) if result.returncode == 0 else False


PATH_OPTIONS = {"--old", "--new", "--out", "--json-out", "--manifest"}


def portable_value(value):
    if not value or value == "-" or value.startswith("-"):
        return value
    candidate = Path(value)
    if not candidate.is_absolute():
        return value
    try:
        return candidate.expanduser().resolve().relative_to(Path.cwd().resolve()).as_posix()
    except (ValueError, OSError):
        return value


def portable_args(argv):
    result = []
    index = 0
    while index < len(argv):
        item = argv[index]
        if item in PATH_OPTIONS and index + 1 < len(argv):
            result.extend([item, portable_value(argv[index + 1])])
            index += 2
            continue
        matched = False
        for option in PATH_OPTIONS:
            if item.startswith(option + "="):
                result.append(option + "=" + portable_value(item[len(option) + 1 :]))
                matched = True
                break
        if not matched:
            result.append(item)
        index += 1
    return result


def regenerate_command():
    script = Path(sys.argv[0])
    if script.exists():
        relative = repo_path(script)
        if not Path(relative).is_absolute() and not relative.startswith("../"):
            return "python3 " + shlex.join([relative, *portable_args(sys.argv[1:])])
    if script.parent.name == "scripts" and script.parent.parent.name:
        portable = f"{script.parent.parent.name}/scripts/{script.name}"
    else:
        portable = script.name
    return "python3 " + shlex.join([portable, *portable_args(sys.argv[1:])])


def write_manifest(path, artifact, outputs, sources, generated_at=None):
    payload = {
        "version": 1,
        "skill": "gorani-api-contract-diff",
        "artifact": artifact,
        "outputs": outputs,
        "sources": sources,
        "generated_commit": git_head_commit(),
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "working_tree_dirty": git_dirty(),
        "regenerate": regenerate_command(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
