#!/usr/bin/env python3
"""기존 산출물의 stale 여부를 값싸게 확인한다.

기본 모드(stale)는 `*.artifact.json` sidecar manifest와 git diff만 사용한다.
코드를 파싱하지 않고, 갱신 대상이 없으면 파일도 출력도 만들지 않는다.

`--mode full`은 릴리스 전이나 사용자가 요청할 때만 쓰는 영향도 요약이다.
산출물을 직접 수정하지 않고 갱신 명령과 확인 범위만 제안한다.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".omo",
    ".gorani",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    "__pycache__",
}
CATEGORY_RULES = {
    "frontend": [
        "src/app/**/page.*",
        "src/app/**/layout.*",
        "src/pages/**",
        "src/routes/**",
        "app/**/page.*",
        "pages/**",
        "**/*.tsx",
        "**/*.jsx",
        "**/*.vue",
        "**/*.svelte",
    ],
    "api": [
        "openapi/**",
        "**/openapi*.yaml",
        "**/openapi*.yml",
        "**/openapi*.json",
        "**/api/**",
        "**/controllers/**",
        "**/routes/**",
    ],
    "db": [
        "db/migrations/**",
        "migrations/**",
        "**/*.sql",
    ],
    "config": [
        ".env*",
        "docker-compose*.yml",
        "docker-compose*.yaml",
        "compose*.yml",
        "compose*.yaml",
        "k8s/**",
        "helm/**",
        "charts/**",
    ],
    "dependencies": [
        "package.json",
        "**/package-lock.json",
        "**/pnpm-lock.yaml",
        "**/yarn.lock",
        "requirements*.txt",
        "pyproject.toml",
        "uv.lock",
        "poetry.lock",
        "go.mod",
        "go.sum",
        "Cargo.toml",
        "Cargo.lock",
        "pom.xml",
        "build.gradle*",
        "gradle.lockfile",
    ],
    "tests": [
        "tests/**",
        "test/**",
        "**/*.test.*",
        "**/*.spec.*",
        "**/*_test.*",
        "**/test_*.py",
    ],
}
SUGGESTIONS = {
    "frontend": (
        "gorani-site-structure",
        "화면·메뉴·레이아웃 영향 여부를 실제 프론트에서 확인하고 구조도를 갱신합니다.",
    ),
    "api": (
        "gorani-api-contract-diff",
        "이전·새 OpenAPI 스펙을 비교해 breaking change와 클라이언트 영향을 확인합니다.",
    ),
    "db": (
        "gorani-table-spec",
        "테이블 명세를 갱신하고 마이그레이션 잠금·데이터 손실 위험을 확인합니다.",
    ),
    "config": (
        "수동 확인",
        ".env.example·compose·Kubernetes manifest의 환경변수가 서로 일치하는지 확인합니다.",
    ),
    "dependencies": (
        "gorani-cve-scan",
        "의존성 CVE와 라이선스 고지 갱신 필요 여부를 확인합니다. 이어서 gorani-dependency-update를 검토합니다.",
    ),
    "tests": (
        "테스트 실행",
        "변경된 테스트와 영향 범위의 테스트를 실행하고 결과를 기록합니다.",
    ),
}
PRIORITY = ["frontend", "api", "db", "config", "dependencies", "tests"]


def parse_args():
    parser = argparse.ArgumentParser(description="기존 산출물의 stale 영향도 확인")
    parser.add_argument(
        "--mode",
        choices=["stale", "full"],
        default="stale",
        help="stale: 값싼 갱신 필요 확인(기본), full: 릴리스용 영향도 요약",
    )
    parser.add_argument("--root", default=".", help="저장소 루트 (기본: 현재 디렉터리)")
    parser.add_argument(
        "--base",
        default="",
        help="manifest에 generated_commit이 없을 때 쓸 fallback ref. full 모드에서는 변경 분류 기준",
    )
    parser.add_argument("--head", default="HEAD", help="비교 끝 ref (기본: HEAD)")
    parser.add_argument(
        "--working",
        action="store_true",
        help="커밋되지 않은 변경과 untracked 파일도 포함",
    )
    parser.add_argument(
        "--manifest-glob",
        default="**/*.artifact.json",
        help="sidecar manifest 탐색 글롭 (기본: **/*.artifact.json)",
    )
    parser.add_argument("--outdir", default=".gorani/impact", help="리포트 출력 디렉터리")
    parser.add_argument(
        "--formats",
        default="md,json",
        help="리포트 형식: md,json (기본: md,json)",
    )
    parser.add_argument("--print", action="store_true", help="Markdown 리포트를 stdout에도 출력")
    parser.add_argument("--force", action="store_true", help="stale이 없어도 리포트 파일 생성")
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="갱신 필요 산출물이 있으면 exit 1",
    )
    parser.add_argument(
        "--fail-on-unknown",
        action="store_true",
        help="manifest를 확인할 수 없으면 exit 1",
    )
    parser.add_argument(
        "--now",
        default="",
        help="테스트용 기준 시각(ISO 8601). 비우면 현재 시각",
    )
    args = parser.parse_args()
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    unknown = [item for item in formats if item not in {"md", "json"}]
    if unknown:
        parser.error(f"지원하지 않는 형식입니다: {', '.join(unknown)}")
    if not formats:
        parser.error("--formats 에 하나 이상의 형식을 지정하세요.")
    args.formats = formats
    return args


def now_iso(value):
    if value:
        return value
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def classify(files):
    categories = {}
    for category in PRIORITY + ["docs"]:
        patterns = CATEGORY_RULES.get(category, [])
        if category == "docs":
            patterns = ["docs/**", "**/*.md", "**/*.adoc"]
        matches = sorted(item for item in files if match_sources(item, patterns))
        if matches:
            categories[category] = matches
    return categories


def build_result(args, root, head_commit, stale, clean, unknown, categories, warnings):
    return {
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


def build_markdown(result):
    summary = result["summary"]
    lines = [
        "# 변경 영향 — " + ("stale 확인" if result["mode"] == "stale" else "전체 요약"),
        "",
        f"- 모드: {result['mode']}",
        f"- 기준: {result['base']}",
        f"- HEAD: {result['head'] or '-'}",
        f"- 기준 시각: {result['generated_at']}",
        f"- 변경 파일: {summary['changed_files']}",
        f"- 갱신 필요: {summary['stale']}",
        f"- 변경 없음: {summary['clean']}",
        f"- 확인 불가: {summary['unknown']}",
    ]
    if result["mode"] == "full" and result["categories"]:
        lines.append("- 변경 분류: " + ", ".join(f"{key} {len(value)}" for key, value in result["categories"].items()))
    lines += ["", "## 갱신 필요", ""]
    if result["stale"]:
        lines += [
            "| 산출물 | 스킬 | 매칭된 변경 | 재생성 |",
            "| --- | --- | --- | --- |",
        ]
        for item in result["stale"]:
            matched = item["matched"][:8]
            text = "<br>".join(matched)
            if len(item["matched"]) > len(matched):
                text += f"<br>외 {len(item['matched']) - len(matched)}건"
            regenerate = item["regenerate"] or "-"
            lines.append(
                f"| `{item['artifact'] or item['manifest']}` | `{item['skill'] or '-'}` | {text or '-'} | `{regenerate}` |"
            )
    else:
        lines.append("- 갱신 필요 없음")
    if result["unknown"]:
        lines += ["", "## 확인 불가", ""]
        for item in result["unknown"]:
            errors = "; ".join(item["errors"]) or "원인 미확인"
            lines.append(f"- `{item['artifact'] or item['manifest']}` — {errors}")
    if result["mode"] == "full":
        lines += ["", "## 변경 분류", ""]
        if result["categories"]:
            for category, files in result["categories"].items():
                lines.append(f"- {category}: {len(files)}건")
                for path in files[:10]:
                    lines.append(f"  - `{path}`")
                if len(files) > 10:
                    lines.append(f"  - 외 {len(files) - 10}건")
        else:
            lines.append("- 분류된 변경 없음")
        lines += ["", "## 확인 제안", ""]
        if result["suggestions"]:
            for item in result["suggestions"]:
                lines.append(f"- `{item['skill']}` — {item['reason']}")
        else:
            lines.append("- 없음")
        lines += ["", "## 릴리스 절차", ""]
        lines.append("- 이 리포트를 확인한 뒤 `gorani-release-check` → `gorani-release-note` 순서로 진행합니다.")
    if result["warnings"]:
        lines += ["", "## 경고", ""]
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
    lines += [
        "",
        "> 이 리포트는 산출물을 수정하지 않습니다. 표시된 갱신 명령을 확인한 뒤 사용자가 직접 실행합니다.",
        "",
    ]
    return "\n".join(lines)


def output_paths(args, root, head_commit):
    head = head_commit[:12] if head_commit else "unknown"
    suffix = "-working" if args.working else ""
    stem = f"impact-{head}-{args.mode}{suffix}"
    outdir = Path(root) / args.outdir
    return outdir, outdir / f"{stem}.md", outdir / f"{stem}.json"


def main():
    args = parse_args()
    root = Path(args.root)
    if not root.is_dir():
        print(f"error: 저장소 루트가 없습니다: {root}", file=sys.stderr)
        return 2
    top, error = run_git(root, "rev-parse", "--show-toplevel")
    if top is None:
        print(f"error: git 저장소가 아닙니다: {root} ({error})", file=sys.stderr)
        return 2
    root = Path(top.strip())
    head_commit = resolve_commit(root, args.head)
    if not head_commit:
        print(f"error: head ref를 찾지 못했습니다: {args.head}", file=sys.stderr)
        return 2
    if not args.base and args.mode == "full":
        detected = default_full_base(root)
        if detected:
            args.base = detected
    if args.base:
        base_commit = resolve_commit(root, args.base)
        if not base_commit:
            print(f"error: base ref를 찾지 못했습니다: {args.base}", file=sys.stderr)
            return 2
    working = working_files(root) if args.working else []
    manifests = discover_manifests(root, args.manifest_glob)
    stale, clean, unknown, warnings = [], [], [], []
    if not manifests:
        warning = f"{args.manifest_glob} 파일을 찾지 못했습니다. 기존 스킬로 산출물을 다시 생성하면 sidecar manifest가 함께 만들어집니다."
        print(f"warning: {warning}", file=sys.stderr)
        warnings.append(warning)
    for path in manifests:
        manifest, _ = load_manifest(path, root)
        result = evaluate(manifest, root, args, head_commit, working)
        if result["status"] == "stale":
            stale.append(result)
        elif result["status"] == "clean":
            clean.append(result)
        else:
            unknown.append(result)
            warnings.extend(f"{manifest['relative']}: {item}" for item in result["errors"])

    bases = {item["base"] for item in [*stale, *clean, *unknown] if item["base"]}
    if args.base:
        bases = {resolve_commit(root, args.base) or head_commit}
    files = set()
    for base in sorted(bases):
        base_files, _ = changed_files(root, base, head_commit)
        files.update(base_files or [])
    if args.working:
        files.update(working)
    files = sorted(files)
    files = [
        item
        for item in files
        if not item.startswith(".gorani/") and not item.endswith(".artifact.json")
    ]
    categories = classify(files) if args.mode == "full" else {}
    categories["_changed"] = len(files)
    result = build_result(args, root, head_commit, stale, clean, unknown, categories, warnings)
    if args.mode == "full":
        seen = set()
        for category in PRIORITY:
            if category in result["categories"]:
                skill, reason = SUGGESTIONS[category]
                if skill not in seen:
                    seen.add(skill)
                    result["suggestions"].append({"skill": skill, "reason": reason, "category": category})
        for item in stale:
            skill = item["manifest"]["skill"] or "산출물 갱신"
            if skill in seen:
                continue
            seen.add(skill)
            result["suggestions"].append(
                {
                    "skill": skill,
                    "reason": f"{item['manifest']['artifact'] or item['manifest']['relative']} 갱신 필요",
                    "category": "stale",
                }
            )

    should_write = args.mode == "full" or bool(stale) or args.force
    markdown = build_markdown(result)
    if should_write:
        outdir, md_path, json_path = output_paths(args, root, head_commit)
        if "md" in args.formats:
            outdir.mkdir(parents=True, exist_ok=True)
            md_path.write_text(markdown, encoding="utf-8")
        if "json" in args.formats:
            outdir.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.print:
            print(markdown)
        else:
            summary = result["summary"]
            if args.mode == "full":
                print(
                    f"full: 변경 {summary['changed_files']}, 갱신 필요 {summary['stale']}, 확인 불가 {summary['unknown']}"
                )
            else:
                print(f"stale: 갱신 필요 {summary['stale']}건")
            if "md" in args.formats:
                print(str(md_path))
            if "json" in args.formats:
                print(str(json_path))
    elif args.print:
        print(markdown)

    if args.fail_on_stale and stale:
        return 1
    if args.fail_on_unknown and unknown:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
