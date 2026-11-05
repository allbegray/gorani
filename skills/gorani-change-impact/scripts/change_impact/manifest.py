"""sidecar `*.artifact.json` manifest를 찾고 읽고 글롭과 매칭한다."""

import json
import re
from pathlib import Path

from .constants import SKIP_DIRS


def repo_path(path, root):
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (Path.cwd() / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        return candidate.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


def split_sources(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


_GLOB_CACHE = {}


def glob_regex(pattern):
    if pattern in _GLOB_CACHE:
        return _GLOB_CACHE[pattern]
    text = pattern.strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    if not text:
        return None
    if "/" not in text:
        text = "**/" + text
    parts = ["^"]
    index = 0
    while index < len(text):
        char = text[index]
        if char == "*":
            if index + 1 < len(text) and text[index + 1] == "*":
                if index + 2 < len(text) and text[index + 2] == "/":
                    parts.append("(?:.*/)?")
                    index += 3
                else:
                    parts.append(".*")
                    index += 2
            else:
                parts.append("[^/]*")
                index += 1
        elif char == "?":
            parts.append("[^/]")
            index += 1
        elif char == "[":
            end = text.find("]", index + 1)
            if end == -1:
                parts.append(re.escape(char))
                index += 1
            else:
                body = text[index + 1 : end]
                if body.startswith("!"):
                    body = "^" + body[1:]
                parts.append("[" + body + "]")
                index = end + 1
        else:
            parts.append(re.escape(char))
            index += 1
    parts.append("$")
    compiled = re.compile("".join(parts))
    _GLOB_CACHE[pattern] = compiled
    return compiled


def match_sources(path, sources):
    positives = [item for item in sources if not item.startswith("!")]
    negatives = [item[1:] for item in sources if item.startswith("!")]
    for pattern in negatives:
        compiled = glob_regex(pattern)
        if compiled and compiled.match(path):
            return False
    for pattern in positives:
        compiled = glob_regex(pattern)
        if compiled and compiled.match(path):
            return True
    return False


def discover_manifests(root, pattern):
    found = []
    for path in sorted(Path(root).rglob(pattern)):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        found.append(path)
    return found


def load_manifest(path, root):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "path": path,
            "relative": repo_path(path, root),
            "skill": "",
            "artifact": "",
            "outputs": [],
            "sources": [],
            "generated_commit": "",
            "generated_at": "",
            "regenerate": "",
            "note": "",
            "error": f"manifest를 읽지 못했습니다: {error}",
        }, ""
    if not isinstance(data, dict):
        return {
            "path": path,
            "relative": repo_path(path, root),
            "skill": "",
            "artifact": "",
            "outputs": [],
            "sources": [],
            "generated_commit": "",
            "generated_at": "",
            "regenerate": "",
            "note": "",
            "error": "manifest가 객체가 아닙니다",
        }, ""
    sources = split_sources(data.get("sources"))
    if not sources:
        return {
            "path": path,
            "relative": repo_path(path, root),
            "skill": str(data.get("skill") or "").strip(),
            "artifact": str(data.get("artifact") or "").strip(),
            "outputs": split_sources(data.get("outputs")),
            "sources": [],
            "generated_commit": str(data.get("generated_commit") or "").strip(),
            "generated_at": str(data.get("generated_at") or "").strip(),
            "regenerate": str(data.get("regenerate") or "").strip(),
            "note": str(data.get("note") or "").strip(),
            "error": "sources 없음",
        }, ""
    return {
        "path": path,
        "relative": repo_path(path, root),
        "skill": str(data.get("skill") or "").strip(),
        "artifact": str(data.get("artifact") or "").strip(),
        "outputs": split_sources(data.get("outputs")),
        "sources": sources,
        "generated_commit": str(data.get("generated_commit") or "").strip(),
        "generated_at": str(data.get("generated_at") or "").strip(),
        "regenerate": str(data.get("regenerate") or "").strip(),
        "note": str(data.get("note") or "").strip(),
        "error": "",
    }, ""


def filter_changed(files, manifest):
    ignored = set(manifest["outputs"])
    ignored.add(manifest["relative"])
    return [
        item
        for item in files
        if item not in ignored
        and not item.endswith(".artifact.json")
        and not item.startswith(".gorani/")
    ]
