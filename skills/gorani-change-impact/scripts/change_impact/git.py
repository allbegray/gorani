"""저장소 루트·기준 commit·변경 파일 목록을 git 명령으로 읽는다."""

import subprocess
from pathlib import Path


def run_git(root, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        return None, str(error)
    if result.returncode != 0:
        return None, result.stderr.strip() or f"git {' '.join(args)} 실패"
    return result.stdout, ""


_COMMIT_CACHE = {}


def resolve_commit(root, ref):
    if not ref:
        return ""
    key = (str(Path(root).resolve()), ref)
    if key in _COMMIT_CACHE:
        return _COMMIT_CACHE[key]
    output, _ = run_git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    value = output.strip() if output else ""
    _COMMIT_CACHE[key] = value
    return value


def is_ancestor(root, ancestor, descendant):
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def last_manifest_commit(root, relative):
    output, _ = run_git(root, "log", "-1", "--format=%H", "--", relative)
    return output.strip() if output else ""


def merge_base(root, left, right):
    output, _ = run_git(root, "merge-base", left, right)
    return output.strip() if output else ""


def default_full_base(root):
    tag, _ = run_git(root, "describe", "--tags", "--abbrev=0", "HEAD")
    if tag:
        tag = tag.strip()
        tag_commit = resolve_commit(root, tag)
        head_commit = resolve_commit(root, "HEAD")
        if tag_commit and tag_commit != head_commit:
            return tag_commit
        previous, _ = run_git(root, "describe", "--tags", "--abbrev=0", "HEAD^")
        if previous and resolve_commit(root, previous.strip()):
            return resolve_commit(root, previous.strip())
    for candidate in ("origin/main", "main"):
        if resolve_commit(root, candidate):
            base = merge_base(root, candidate, "HEAD")
            if base and base != resolve_commit(root, "HEAD"):
                return base
    if resolve_commit(root, "HEAD~1"):
        return resolve_commit(root, "HEAD~1")
    return ""


_DIFF_CACHE = {}


def changed_files(root, base, head):
    key = (str(Path(root).resolve()), base, head)
    if key in _DIFF_CACHE:
        return list(_DIFF_CACHE[key]), ""
    output, error = run_git(root, "diff", "--name-only", "-z", f"{base}..{head}")
    if output is None:
        return None, error
    value = [item for item in output.split("\0") if item]
    _DIFF_CACHE[key] = value
    return list(value), ""


def working_files(root):
    files = set()
    output, _ = run_git(root, "diff", "--name-only", "-z", "HEAD")
    if output:
        files.update(item for item in output.split("\0") if item)
    output, _ = run_git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if output:
        files.update(item for item in output.split("\0") if item)
    return sorted(files)
