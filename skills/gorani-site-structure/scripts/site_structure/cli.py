"""site-structure CLI. 입력을 읽고 리포트 모델을 만든 뒤 렌더러를 호출한다."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_FORMATS, OUTPUT_FORMATS
from .input import load_input
from .manifest import repo_path, write_manifest
from .model import build_report_model
from .render_html import build_html
from .render_md import build_markdown


def parse_args():
    parser = argparse.ArgumentParser(description="사이트 구조도 산출물 생성")
    parser.add_argument("--input", required=True, help="정규화된 사이트 구조 JSON")
    parser.add_argument("--outdir", default="docs/site-structure", help="출력 디렉터리")
    parser.add_argument("--name", default="site-structure", help="출력 파일 기본 이름")
    parser.add_argument(
        "--formats",
        default=DEFAULT_FORMATS,
        help=f"생성할 산출물: {','.join(OUTPUT_FORMATS)} (기본: {DEFAULT_FORMATS})",
    )
    parser.add_argument(
        "--sources",
        default="",
        help="산출물 갱신 판단에 쓸 소스 글롭 (쉼표 구분). 기본은 입력 JSON과 src/app·src/pages·src/routes",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="sidecar .artifact.json manifest를 만들지 않음",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="검증 경고가 있으면 종료 코드 1",
    )
    parser.add_argument(
        "--model-out",
        help="렌더링 전 리포트 모델 JSON을 추가로 저장할 경로",
    )
    parser.add_argument(
        "--generated-at",
        help="생성 시각 강제 지정 (ISO 8601, 샘플 재생성용)",
    )
    args = parser.parse_args()
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    unknown = [item for item in formats if item not in OUTPUT_FORMATS]
    if unknown:
        parser.error(f"지원하지 않는 형식입니다: {', '.join(unknown)}")
    if not formats:
        parser.error("--formats 에 하나 이상의 형식을 지정하세요.")
    args.formats = set(formats)
    return args


def resolve_sources(args, meta):
    if args.sources:
        sources = [item.strip() for item in args.sources.split(",") if item.strip()]
    elif meta["sources"]:
        sources = meta["sources"]
    else:
        sources = [repo_path(args.input)]
        for candidate in ("src/app", "src/pages", "src/routes"):
            if (Path.cwd() / candidate).is_dir():
                sources.append(candidate + "/**")
    unique_sources = []
    for item in sources:
        if item not in unique_sources:
            unique_sources.append(item)
    return unique_sources


def write_model(model, path):
    model_path = Path(path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        model_path.write_text(
            json.dumps(model, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        sys.exit(f"리포트 모델을 저장하지 못했습니다: {exc}")


def main():
    args = parse_args()
    meta, pages, depth_count, warnings, standards, api_only = load_input(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = outdir / f"{args.name}.md"
    html_path = outdir / f"{args.name}.html"
    xlsx_path = outdir / f"{args.name}.xlsx"
    sources = resolve_sources(args, meta)
    generated_at = args.generated_at or datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    model = build_report_model(
        meta,
        pages,
        depth_count,
        warnings,
        standards,
        api_only,
        sources,
        generated_at,
    )

    if args.model_out:
        write_model(model, args.model_out)

    if "md" in args.formats:
        md_path.write_text(build_markdown(model), encoding="utf-8")
    if "html" in args.formats:
        html_path.write_text(build_html(model), encoding="utf-8")
    if "xlsx" in args.formats:
        from .render_xlsx import write_xlsx

        write_xlsx(xlsx_path, model)
    outputs = []
    for key, path in (("md", md_path), ("html", html_path), ("xlsx", xlsx_path)):
        if key in args.formats:
            outputs.append(repo_path(path))
    manifest_path = outdir / f"{args.name}.artifact.json"
    if not args.no_manifest:
        write_manifest(
            manifest_path,
            repo_path(
                xlsx_path if "xlsx" in args.formats else outputs[0] if outputs else outdir
            ),
            outputs,
            sources,
            generated_at=generated_at,
        )
    summary = {
        "md": str(md_path) if "md" in args.formats else "",
        "html": str(html_path) if "html" in args.formats else "",
        "xlsx": str(xlsx_path) if "xlsx" in args.formats else "",
        "pages": model["summary"]["pages"],
        "depth": model["summary"]["depth"],
        "api_mappings": model["summary"]["api_mappings"],
        "api_only": model["summary"]["api_only"],
        "standards": model["summary"]["standards"],
        "warnings": model["summary"]["warnings"],
        "manifest": "" if args.no_manifest else str(manifest_path),
    }
    if args.model_out:
        summary["model"] = str(args.model_out)
    print(json.dumps(summary, ensure_ascii=False))
    if args.strict and warnings:
        sys.exit(1)
    return 0
