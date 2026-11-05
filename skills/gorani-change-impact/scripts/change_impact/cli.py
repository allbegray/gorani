"""change-impact CLI. argparse, 경로 결정, 모델 생성, 렌더러 호출."""

import argparse
import sys
from pathlib import Path

from .classify import classify
from .constants import PRIORITY, SUGGESTIONS
from .evaluate import evaluate
from .git import changed_files, default_full_base, resolve_commit, run_git, working_files
from .manifest import discover_manifests, load_manifest
from .model import build_result
from .render_json import render_json
from .render_md import build_markdown


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
        dest="now",
        default="",
        help="테스트용 기준 시각(ISO 8601). 비우면 현재 시각",
    )
    parser.add_argument(
        "--generated-at",
        dest="now",
        help="생성 시각 강제 지정 (ISO 8601, --now와 같음)",
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
            render_json(result, json_path)
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
