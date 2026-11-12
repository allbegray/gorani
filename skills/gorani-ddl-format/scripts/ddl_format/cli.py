"""ddl-format CLI. dump SQL을 읽어 사람이 작성한 스타일의 DDL로 바꾼다."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_FORMATS, DIALECTS, OUTPUT_FORMATS, SCHEMA_VERSION
from .parse import parse_dump
from .render_review import build_review
from .render_sql import Options, render


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="DB dump SQL을 사람이 작성한 스타일의 DDL로 변환",
    )
    parser.add_argument("--input", action="append", help="dump SQL 파일. 여러 번 지정할 수 있음")
    parser.add_argument("--outdir", default="docs/db", help="출력 디렉터리")
    parser.add_argument("--name", default="schema", help="출력 파일 기본 이름")
    parser.add_argument(
        "--dialect",
        default="auto",
        choices=["auto", *DIALECTS],
        help="SQL 방언 (기본: auto)",
    )
    parser.add_argument(
        "--formats",
        default=DEFAULT_FORMATS,
        help=f"생성할 산출물: {','.join(OUTPUT_FORMATS)} (기본: {DEFAULT_FORMATS})",
    )
    parser.add_argument("--title", default="", help="출력 DDL 맨 위에 넣을 설명")
    parser.add_argument("--database", default="", help="DDL 머리말에 넣을 DB 이름")
    parser.add_argument(
        "--strip-schema",
        default="",
        help="출력에서 생략할 스키마. 예: public. 기본은 postgres면 public을 생략",
    )
    parser.add_argument(
        "--keep-schema",
        action="store_true",
        help="--strip-schema 기본값을 쓰지 않고 스키마를 그대로 표시",
    )
    parser.add_argument(
        "--comments",
        default="inline",
        choices=["inline", "text", "off"],
        help="주석 처리: inline(COMMENT ON·COMMENT ''), text(주석 줄), off (기본: inline)",
    )
    parser.add_argument(
        "--keep-names",
        action="store_true",
        help="pg_dump가 만든 제약·인덱스 이름을 그대로 둠",
    )
    parser.add_argument(
        "--no-serial",
        action="store_true",
        help="bigint + nextval을 bigserial로 바꾸지 않음",
    )
    parser.add_argument(
        "--no-align",
        action="store_true",
        help="컬럼 타입 시작 위치를 세로로 맞추지 않음",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="출력 DDL의 머리말 주석을 넣지 않음",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="경고가 있으면 종료 코드 1",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="변환에서 빠진 객체·이름 변경·경고를 담은 검토 md를 함께 생성",
    )
    parser.add_argument(
        "--model-out",
        help="렌더링 전 리포트 모델 JSON을 저장할 경로",
    )
    parser.add_argument(
        "--generated-at",
        help="생성 시각 강제 지정 (ISO 8601, 샘플 재생성용)",
    )
    args = parser.parse_args(argv)
    if not args.input:
        parser.error("--input 을 지정하세요.")
    formats = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    unknown = [item for item in formats if item not in OUTPUT_FORMATS]
    if unknown:
        parser.error(f"지원하지 않는 형식입니다: {', '.join(unknown)}")
    if not formats:
        parser.error("--formats 에 하나 이상의 형식을 지정하세요.")
    args.formats = set(formats)
    return args


def collect_inputs(paths):
    files = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            candidates = sorted(
                item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".sql", ".ddl"}
            )
        elif path.is_file():
            candidates = [path]
        else:
            sys.exit(f"입력 파일이 없습니다: {raw}")
        files.extend(candidates)
    if not files:
        sys.exit("SQL 파일을 찾지 못했습니다. --input 경로를 확인하세요.")
    return files


def read_inputs(files):
    chunks = []
    for path in files:
        try:
            chunks.append(path.read_text(encoding="utf-8-sig"))
        except UnicodeDecodeError:
            chunks.append(path.read_text(encoding="latin-1"))
    return "\n\n".join(chunks)


def build_model(result, args, generated_at, files, outputs):
    tables = []
    for table in sorted(result.tables.values(), key=lambda item: (item["schema"], item["name"])):
        tables.append(
            {
                "schema": table["schema"],
                "name": table["name"],
                "comment": table["comment"],
                "columns": len(table["columns"]),
                "primary_key": (table["primary_key"] or {}).get("columns", []),
                "foreign_keys": [
                    {
                        "name": item["name"],
                        "columns": item["columns"],
                        "ref_schema": item["ref_schema"],
                        "ref_table": item["ref_table"],
                        "ref_columns": item["ref_columns"],
                        "on_delete": item["on_delete"],
                        "on_update": item["on_update"],
                    }
                    for item in table["foreign_keys"]
                ],
                "uniques": table["uniques"],
                "checks": table["checks"],
                "indexes": [
                    {
                        "name": item["name"],
                        "columns": item["columns"],
                        "unique": item["unique"],
                        "where": item["where"],
                    }
                    for item in table["indexes"]
                ],
                "source_line": table["source_line"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "generated_at": generated_at,
            "dialect": result.dialect,
            "files": [str(path) for path in files],
            "generator": "gorani-ddl-format",
            "options": {
                "comments": args.comments,
                "strip_schema": strip_schema(args, result.dialect),
                "rename_constraints": not args.keep_names,
                "serial": not args.no_serial,
                "align": not args.no_align,
            },
        },
        "summary": {
            "tables": len(tables),
            "columns": sum(item["columns"] for item in tables),
            "foreign_keys": sum(len(item["foreign_keys"]) for item in tables),
            "indexes": sum(len(item["indexes"]) for item in tables),
            "checks": sum(len(item["checks"]) for item in tables),
            "uniques": sum(len(item["uniques"]) for item in tables),
            "warnings": len(result.warnings),
            "skipped_statements": result.skipped,
        },
        "tables": tables,
        "enums": [
            {"schema": item.get("schema", ""), "name": item["name"], "values": item.get("values", [])}
            for item in result.types
        ],
        "sequences": result.sequences,
        "schemas": result.schemas,
        "warnings": list(result.warnings),
        "outputs": outputs,
    }


def strip_schema(args, dialect):
    if args.keep_schema:
        return ""
    if args.strip_schema:
        return args.strip_schema
    return "public" if dialect == "postgres" else ""


def main(argv=None):
    args = parse_args(argv)
    files = collect_inputs(args.input)
    text = read_inputs(files)

    result = parse_dump(text, args.dialect)
    if not result.tables:
        sys.exit(
            "테이블을 찾지 못했습니다. dump 파일인지, --dialect가 맞는지 확인하세요. "
            f"건너뛴 문장 {result.skipped}개"
        )

    generated_at = args.generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    options = Options(
        dialect=result.dialect,
        strip_schema=strip_schema(args, result.dialect),
        comments=args.comments,
        rename_constraints=not args.keep_names,
        serial=not args.no_serial,
        header=not args.no_header,
        title=args.title,
        database=args.database,
        align=not args.no_align,
    )
    ddl = render(result, options)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sql_path = outdir / f"{args.name}.sql"
    review_path = outdir / f"{args.name}.review.md"

    outputs = []
    if "sql" in args.formats:
        sql_path.write_text(ddl, encoding="utf-8")
        outputs.append(str(sql_path))
    if "review" in args.formats or args.review:
        review_path.write_text(build_review(result, options, files, generated_at), encoding="utf-8")
        outputs.append(str(review_path))

    model_path = None
    if args.model_out:
        model_path = Path(args.model_out)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(
            json.dumps(build_model(result, args, generated_at, files, outputs), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )

    summary = {
        "sql": str(sql_path) if "sql" in args.formats else "",
        "review": str(review_path) if review_path.exists() else "",
        "dialect": result.dialect,
        "tables": len(result.tables),
        "columns": sum(len(table["columns"]) for table in result.tables.values()),
        "warnings": len(result.warnings),
        "skipped_statements": result.skipped,
    }
    if model_path is not None:
        summary["model"] = str(model_path)
    print(json.dumps(summary, ensure_ascii=False))
    if args.strict and result.warnings:
        return 1
    return 0
