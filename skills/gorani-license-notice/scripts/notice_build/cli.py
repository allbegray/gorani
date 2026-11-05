"""license-notice CLI. 입력을 읽고 리포트 모델을 만든 뒤 렌더러를 호출한다."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_FORMATS, OUTPUT_FORMATS, SIMPLE_FORMATS, STATUS_LABELS
from .model import build_report_model, group_notices, normalize_packages
from .render_html import build_html, build_simple_html
from .render_md import build_markdown, build_simple_markdown
from .review import build_review_markdown, review_items


def parse_args():
    parser = argparse.ArgumentParser(description="오픈소스 고지 페이지 생성")
    parser.add_argument("--input", required=True, help="정규화된 라이선스 JSON 경로")
    parser.add_argument("--outdir", default="docs/licenses", help="출력 디렉터리")
    parser.add_argument("--name", default="third-party-notices", help="출력 파일 기본 이름")
    parser.add_argument(
        "--formats",
        default=None,
        help=f"생성할 산출물: {','.join(OUTPUT_FORMATS)} (기본: {DEFAULT_FORMATS}, --simple: html,md)",
    )
    parser.add_argument("--xlsx", action="store_true", help="--formats 에 xlsx 추가 (openpyxl 필요)")
    parser.add_argument(
        "--simple",
        "--minimal",
        dest="simple",
        action="store_true",
        help="라이선스 전문 없이 이름·버전·GitHub 라이선스 링크만 담은 간소화 페이지 생성",
    )
    parser.add_argument("--exclude-dev", action="store_true", help="scope 가 dev 인 패키지 제외")
    parser.add_argument(
        "--fail-on-review",
        action="store_true",
        help="검토 필요 항목이 있으면 종료 코드 1",
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
    if args.simple and args.xlsx:
        parser.error("--simple 과 --xlsx 는 함께 쓸 수 없습니다.")
    if args.formats is None:
        raw_formats = "html,md" if args.simple else DEFAULT_FORMATS
    else:
        raw_formats = args.formats
    formats = [item.strip().lower() for item in raw_formats.split(",") if item.strip()]
    allowed = SIMPLE_FORMATS if args.simple else OUTPUT_FORMATS
    unknown = [item for item in formats if item not in allowed]
    if unknown:
        parser.error(f"지원하지 않는 형식입니다: {', '.join(unknown)}")
    if not formats:
        parser.error("--formats 에 하나 이상의 형식을 지정하세요.")
    args.formats = set(formats)
    if args.xlsx:
        args.formats.add("xlsx")
    return args


def write_model(model, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(
            json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as error:
        sys.exit(f"리포트 모델을 저장하지 못했습니다: {error}")
    return target


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_file():
        sys.exit(f"입력 파일이 없습니다: {input_path}")
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"입력 JSON 을 읽지 못했습니다: {error}")
    raw_packages = data.get("packages")
    if not isinstance(raw_packages, list) or not raw_packages:
        sys.exit("입력 JSON 의 packages 배열이 비어 있습니다.")
    if args.exclude_dev:
        raw_packages = [
            item for item in raw_packages if str(item.get("scope", "")).strip().lower() != "dev"
        ]
        if not raw_packages:
            sys.exit("--exclude-dev 적용 후 대상 패키지가 없습니다.")

    packages = normalize_packages(raw_packages)
    if not packages:
        sys.exit("정규화된 패키지가 없습니다. 입력 형식을 확인하세요.")
    if args.generated_at:
        data["generated_at"] = args.generated_at
    else:
        data.setdefault("generated_at", datetime.now().astimezone().isoformat(timespec="seconds"))
    review = review_items(packages)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.simple:
        model = build_report_model(data, packages, [], review, args.name, mode="simple")
        model_path = write_model(model, args.model_out) if args.model_out else None
        simple_html_path = outdir / f"{args.name}-simple.html"
        simple_md_path = outdir / f"{args.name}-simple.md"
        if "html" in args.formats:
            simple_html_path.write_text(build_simple_html(model), encoding="utf-8")
        if "md" in args.formats:
            simple_md_path.write_text(build_simple_markdown(model), encoding="utf-8")
        simple_summary = {
            "mode": "simple",
            "formats": [item for item in SIMPLE_FORMATS if item in args.formats],
            "simple_html": str(simple_html_path) if "html" in args.formats else "",
            "simple_md": str(simple_md_path) if "md" in args.formats else "",
            "packages": model["summary"]["packages"],
            "missing_github_links": model["summary"]["missing_github_links"],
            "review_items": model["summary"]["review_items"],
        }
        if model_path:
            simple_summary["model"] = str(model_path)
        print(json.dumps(simple_summary, ensure_ascii=False))
        if args.fail_on_review and review:
            sys.exit(1)
        return 0

    groups = group_notices(packages)
    model = build_report_model(data, packages, groups, review, args.name)
    model_path = write_model(model, args.model_out) if args.model_out else None
    html_path = outdir / f"{args.name}.html"
    md_path = outdir / f"{args.name}.md"
    review_path = outdir / f"{args.name}-review.md"
    xlsx_path = outdir / f"{args.name}.xlsx"

    if "html" in args.formats:
        html_path.write_text(build_html(model), encoding="utf-8")
    if "md" in args.formats:
        md_path.write_text(build_markdown(model), encoding="utf-8")
    if "review" in args.formats:
        if review:
            review_path.write_text(build_review_markdown(model), encoding="utf-8")
        elif review_path.exists():
            review_path.unlink()
    if "xlsx" in args.formats:
        from .render_xlsx import write_workbook

        write_workbook(xlsx_path, model, args.name)

    summary = {
        "formats": [item for item in OUTPUT_FORMATS if item in args.formats],
        "html": str(html_path) if "html" in args.formats else "",
        "md": str(md_path) if "md" in args.formats else "",
        "review": str(review_path) if review and "review" in args.formats else "",
        "xlsx": str(xlsx_path) if "xlsx" in args.formats else "",
        "packages": model["summary"]["packages"],
        "licenses": model["summary"]["licenses"],
        "license_texts": model["summary"]["license_texts"],
        "review_items": model["summary"]["review_items"],
        "status": {
            STATUS_LABELS[key]: value
            for key, value in model["summary"]["status"].items()
        },
    }
    if model_path:
        summary["model"] = str(model_path)
    print(json.dumps(summary, ensure_ascii=False))

    if args.fail_on_review and review:
        sys.exit(1)
    return 0
