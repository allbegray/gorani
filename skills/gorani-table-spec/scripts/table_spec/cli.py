"""table-spec CLI. 입력을 읽고 리포트 모델을 만든 뒤 렌더러를 호출한다."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_FORMATS, DIALECTS, OUTPUT_FORMATS
from .db import introspect_db
from .ddl import collect_files, parse_ddl
from .manifest import repo_path, write_manifest
from .model import build_report_model, finalize_tables
from .render_html import build_html
from .render_md import build_markdown
from .render_xlsx import write_xlsx


def parse_args():
    parser = argparse.ArgumentParser(description="SQL DDL에서 테이블 명세서 생성")
    parser.add_argument(
        "--ddl",
        action="append",
        help="SQL 파일 또는 디렉터리. 여러 번 지정할 수 있음",
    )
    parser.add_argument(
        "--db-url",
        help="SQLAlchemy DB URL. 예: postgresql+psycopg://user:pass@host/db, mysql+pymysql://..., sqlite:///path",
    )
    parser.add_argument(
        "--schema",
        action="append",
        default=[],
        help="DB 모드에서 조회할 스키마. 여러 번 지정할 수 있음 (기본: DB 기본 스키마)",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="DB 모드에서 시스템 테이블도 포함",
    )
    parser.add_argument(
        "--dialect",
        default="auto",
        choices=["auto", *DIALECTS],
        help="SQL 방언 (기본: auto)",
    )
    parser.add_argument("--outdir", default="docs/db", help="출력 디렉터리")
    parser.add_argument("--name", default="table-spec", help="출력 파일 기본 이름")
    parser.add_argument("--project", default="", help="프로젝트명 (기본: 저장소 폴더명)")
    parser.add_argument(
        "--formats",
        default=DEFAULT_FORMATS,
        help=f"생성할 산출물: {','.join(OUTPUT_FORMATS)} (기본: {DEFAULT_FORMATS})",
    )
    parser.add_argument(
        "--sources",
        default="",
        help="산출물 갱신 판단에 쓸 소스 글롭 (쉼표 구분). 기본은 --ddl 경로",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="sidecar .artifact.json manifest를 만들지 않음",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="파싱 경고가 있으면 종료 코드 1",
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
    if not args.ddl and not args.db_url:
        parser.error("--ddl 또는 --db-url 중 하나를 지정하세요.")
    if args.ddl and args.db_url:
        parser.error("--ddl 과 --db-url 은 함께 쓸 수 없습니다.")
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    unknown = [item for item in formats if item not in OUTPUT_FORMATS]
    if unknown:
        parser.error(f"지원하지 않는 형식입니다: {', '.join(unknown)}")
    if not formats:
        parser.error("--formats 에 하나 이상의 형식을 지정하세요.")
    args.formats = set(formats)
    return args


def source_globs(args):
    if args.sources:
        return [item.strip() for item in args.sources.split(",") if item.strip()]
    if args.ddl:
        sources = []
        for raw in args.ddl:
            candidate = Path(raw)
            source = repo_path(candidate) + ("/**" if candidate.is_dir() else "")
            if source not in sources:
                sources.append(source)
        return sources
    return []


def write_model(path, model):
    model_path = Path(path)
    try:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(
            json.dumps(model, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as error:
        sys.exit(f"리포트 모델을 저장하지 못했습니다: {error}")
    return model_path


def main():
    args = parse_args()
    if args.db_url:
        tables, warnings, dialects, source_label = introspect_db(
            args.db_url, args.schema, [], include_system=args.include_system
        )
        files = []
        source = "database"
    else:
        files = collect_files(args.ddl)
        tables, warnings, dialects = parse_ddl(files, args.dialect)
        source_label = f"DDL 파일 {len(files)}개"
        source = "ddl"
    if not tables:
        sys.exit("테이블을 찾지 못했습니다. DDL·DB URL과 --dialect·--schema를 확인하세요.")
    tables = finalize_tables(tables)
    generated_at = args.generated_at or datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    sources = source_globs(args)
    model = build_report_model(
        args.project or Path.cwd().name,
        generated_at,
        dialects,
        files,
        source,
        source_label,
        tables,
        warnings,
        sources,
    )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = outdir / f"{args.name}.md"
    html_path = outdir / f"{args.name}.html"
    xlsx_path = outdir / f"{args.name}.xlsx"
    if "md" in args.formats:
        md_path.write_text(build_markdown(model), encoding="utf-8")
    if "html" in args.formats:
        html_path.write_text(build_html(model), encoding="utf-8")
    if "xlsx" in args.formats:
        write_xlsx(xlsx_path, model)
    outputs = []
    for key, path in (("md", md_path), ("html", html_path), ("xlsx", xlsx_path)):
        if key in args.formats:
            outputs.append(repo_path(path))

    model_path = write_model(args.model_out, model) if args.model_out else None

    note = ""
    if source == "database" and not sources:
        note = "DB 접속 시점 스키마 기준입니다. 변경 감지에 쓰려면 --sources로 마이그레이션 글롭을 지정하세요."
    manifest_path = outdir / f"{args.name}.artifact.json"
    if not args.no_manifest:
        primary = repo_path(xlsx_path if "xlsx" in args.formats else outputs[0] if outputs else outdir)
        write_manifest(
            manifest_path,
            primary,
            outputs,
            sources,
            note,
            generated_at=generated_at,
        )
    summary = {
        "md": str(md_path) if "md" in args.formats else "",
        "html": str(html_path) if "html" in args.formats else "",
        "xlsx": str(xlsx_path) if "xlsx" in args.formats else "",
        "tables": model["summary"]["tables"],
        "columns": model["summary"]["columns"],
        "foreign_keys": model["summary"]["foreign_keys"],
        "indexes": model["summary"]["indexes"],
        "warnings": model["summary"]["warnings"],
        "dialects": model["meta"]["dialects"],
        "manifest": "" if args.no_manifest else str(manifest_path),
        "sources": sources,
    }
    if model_path is not None:
        summary["model"] = str(model_path)
    print(json.dumps(summary, ensure_ascii=False))
    if args.strict and warnings:
        return 1
    return 0
