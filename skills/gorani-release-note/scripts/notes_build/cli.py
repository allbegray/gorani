"""릴리스 노트 CLI. 입력을 읽고 모델을 만든 뒤 렌더러를 호출한다."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_FORMATS, LABELS, OUTPUT_FORMATS
from .model import build_report_model, text
from .render_html import render_html
from .render_internal import render_internal
from .render_json import render_model
from .render_md import render_markdown
from .render_text import render_short, render_store
from .validate import validate


def parse_args():
    parser = argparse.ArgumentParser(description="고객용 릴리스 노트 생성")
    parser.add_argument("--input", required=True, help="큐레이션된 릴리스 노트 JSON")
    parser.add_argument("--outdir", default="docs/releases", help="출력 디렉터리")
    parser.add_argument("--name", default="release-notes", help="출력 파일 기본 이름")
    parser.add_argument(
        "--formats",
        default=DEFAULT_FORMATS,
        help=f"생성할 산출물: {','.join(OUTPUT_FORMATS)} (기본: {DEFAULT_FORMATS})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="commit 매핑 누락, 지원 경로 누락, 잘못된 링크를 오류로 처리",
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


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_file():
        sys.exit(f"입력 파일이 없습니다: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"입력 JSON 을 읽지 못했습니다: {error}")
    if not isinstance(data, dict):
        sys.exit("입력 JSON 의 최상위가 객체가 아닙니다.")

    errors, warnings, strict_issues, limits = validate(data, args.formats)
    if errors:
        print(json.dumps({"errors": errors, "warnings": warnings, "strict": strict_issues}, ensure_ascii=False))
        sys.exit(1)
    if args.strict and strict_issues:
        print(json.dumps({"errors": strict_issues, "warnings": warnings}, ensure_ascii=False))
        sys.exit(1)

    language = text(data.get("language")) or "ko"
    if language not in LABELS:
        warnings.append(f"지원하지 않는 언어 코드입니다. ko 로 표시합니다: {language}")
        language = "ko"
    labels = LABELS[language]

    generated_at = (
        args.generated_at
        or text(data.get("generated_at"))
        or datetime.now().astimezone().isoformat(timespec="seconds")
    )
    model = build_report_model(
        data,
        args.input,
        args.formats,
        labels,
        language,
        limits,
        warnings,
        strict_issues,
        errors,
        generated_at,
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = outdir / f"{args.name}.md"
    html_path = outdir / f"{args.name}.html"
    short_path = outdir / f"{args.name}-short.txt"
    store_path = outdir / f"{args.name}-store.txt"
    internal_path = outdir / f"{args.name}-internal.md"

    model_path = None
    if args.model_out:
        try:
            model_path = render_model(model, args.model_out)
        except OSError as error:
            sys.exit(f"리포트 모델을 저장하지 못했습니다: {error}")

    if "md" in args.formats:
        md_path.write_text(render_markdown(model), encoding="utf-8")
    if "html" in args.formats:
        html_path.write_text(render_html(model), encoding="utf-8")
    if "short" in args.formats:
        short_path.write_text(render_short(model), encoding="utf-8")
    if "store" in args.formats:
        store_path.write_text(render_store(model), encoding="utf-8")
    if "internal" in args.formats:
        internal_path.write_text(render_internal(model), encoding="utf-8")

    summary = model["summary"]
    result = {
        "formats": model["meta"]["formats"],
        "md": str(md_path) if "md" in args.formats else "",
        "html": str(html_path) if "html" in args.formats else "",
        "short": str(short_path) if "short" in args.formats else "",
        "store": str(store_path) if "store" in args.formats else "",
        "internal": str(internal_path) if "internal" in args.formats else "",
        "sections": summary["sections"],
        "highlights": summary["highlights"],
        "commits": summary["commits"],
        "included": summary["included"],
        "excluded": summary["excluded"],
        "short_chars": summary["short_chars"],
        "short_limit": summary["short_limit"],
        "store_chars": summary["store_chars"],
        "store_limit": summary["store_limit"],
        "auto_summary": summary["auto_summary"],
        "warnings": model["warnings"],
        "strict_issues": model["strict_issues"],
    }
    if model_path is not None:
        result["model"] = str(model_path)
    print(json.dumps(result, ensure_ascii=False))
