#!/usr/bin/env python3
"""Check relative Markdown links and anchors in a spec-analysis package.

Usage:
    python3 check_links.py <directory>

Exits 0 when every relative link resolves to an existing file and anchor.
Exits 1 when a link or anchor is missing.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys


LINK_RE = re.compile(r"\]\(([^)]+)\)")
ANCHOR_RE = re.compile(r'<a\s+(?:id|name)="([^"]+)"')


def slug(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s가-힣-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text)


def collect_anchors(path: pathlib.Path) -> set[str]:
    anchors: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        anchors.update(ANCHOR_RE.findall(line))
        if line.startswith("#"):
            anchors.add(slug(line.lstrip("#").strip()))
    return anchors


def check(directory: pathlib.Path) -> list[str]:
    files = {path.name: path for path in sorted(directory.glob("*.md"))}
    if not files:
        return [f"no markdown files in {directory}"]

    anchors = {name: collect_anchors(path) for name, path in files.items()}
    problems: list[str] = []

    for name, path in files.items():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for target in LINK_RE.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                file_part, _, anchor = target.partition("#")
                if file_part not in files:
                    problems.append(f"{name}:{line_no}: missing file: {target}")
                    continue
                if anchor and anchor not in anchors[file_part]:
                    problems.append(f"{name}:{line_no}: missing anchor: {target}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=pathlib.Path)
    args = parser.parse_args()

    problems = check(args.directory)
    if problems:
        print("\n".join(problems))
        print(f"\n{len(problems)} broken link(s)", file=sys.stderr)
        return 1

    count = sum(
        len(LINK_RE.findall(path.read_text(encoding="utf-8")))
        for path in args.directory.glob("*.md")
    )
    print(f"{count} relative link(s), 0 broken")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
