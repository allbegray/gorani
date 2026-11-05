"""대상 스킬의 SKILL.md 메타데이터와 실행 환경을 수집한다."""

import os
import platform
import re
import sys
from pathlib import Path

from .github import run_command


def git_value(root, *args):
    result, _ = run_command(["git", "-C", str(root), *args])
    if result is None or result.returncode != 0:
        return ""
    return result.stdout.strip()


def skill_repo_root():
    # scripts/report_issue/environment.py -> scripts/report_issue -> scripts
    # -> gorani-report -> skills -> 저장소 루트
    return Path(__file__).resolve().parents[4]


def skill_candidates(skill):
    roots = [
        Path.cwd() / ".opencode" / "skills",
        Path.cwd() / ".claude" / "skills",
        Path.cwd() / ".agents" / "skills",
        Path.cwd() / "skills",
        Path.home() / ".config" / "opencode" / "skills",
        Path.home() / ".claude" / "skills",
        Path.home() / ".agents" / "skills",
        skill_repo_root() / "skills",
    ]
    seen = set()
    for root in roots:
        path = root / skill / "SKILL.md"
        if path in seen:
            continue
        seen.add(path)
        yield path


def read_skill_metadata(skill):
    for path in skill_candidates(skill):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not match:
            continue
        metadata = {}
        in_metadata = False
        for line in match.group(1).splitlines():
            if line.strip() == "metadata:":
                in_metadata = True
                continue
            if in_metadata:
                if line.startswith("  ") and ":" in line:
                    key, value = line.strip().split(":", 1)
                    metadata[key.strip()] = value.strip().strip('"').strip("'")
                elif line and not line.startswith(" "):
                    in_metadata = False
        return metadata, path
    return {}, None


def environment_rows(args):
    root = skill_repo_root()
    commit = git_value(root, "rev-parse", "--short", "HEAD") or "unknown"
    dirty = bool(git_value(root, "status", "--porcelain"))
    shell = Path(os.environ.get("SHELL", "")).name or "unknown"
    rows = [
        {"label": "스킬", "value": args.skill},
        {"label": "스킬 버전", "value": args.skill_version},
    ]
    if args.skill_updated:
        rows.append({"label": "스킬 갱신일", "value": args.skill_updated})
    rows += [
        {"label": "skill source commit", "value": commit + ("+dirty" if dirty else "")},
        {"label": "OS", "value": platform.platform()},
        {"label": "Python", "value": sys.version.split()[0]},
        {"label": "Shell", "value": shell},
    ]
    if args.tool:
        rows.append({"label": "도구", "value": "\n".join(args.tool)})
    return rows
