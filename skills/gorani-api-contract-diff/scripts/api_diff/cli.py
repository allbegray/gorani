"""api-contract-diff CLI. 스펙 비교 후 모델을 만들고 렌더러를 호출한다."""

import argparse
from datetime import datetime
from pathlib import Path

from .compare import compare_specs, load_spec
from .manifest import repo_path, write_manifest
from .model import build_report_model
from .render_json import render_json
from .render_md import markdown_report


def parse_args():
    parser = argparse.ArgumentParser(description="OpenAPI 3.x 계약 변경 리포트")
    parser.add_argument("--old", required=True, help="이전 OpenAPI 스펙 (JSON/YAML)")
    parser.add_argument("--new", required=True, help="새 OpenAPI 스펙 (JSON/YAML)")
    parser.add_argument("--out", default="api-diff.md", help="Markdown 출력 경로. '-' 이면 stdout")
    parser.add_argument("--json-out", help="findings JSON 출력 경로")
    parser.add_argument("--service", default="", help="서비스명")
    parser.add_argument("--release-version", default="", help="배포 버전")
    parser.add_argument("--clients", default="", help="영향을 받는 클라이언트 목록 (쉼표 구분)")
    parser.add_argument("--sources", default="", help="산출물 갱신 판단에 쓸 소스 글롭 (쉼표 구분). 기본은 이전·새 스펙 경로")
    parser.add_argument("--manifest", help="sidecar .artifact.json 출력 경로. 기본은 리포트 옆")
    parser.add_argument("--no-manifest", action="store_true", help="sidecar .artifact.json manifest를 만들지 않음")
    parser.add_argument("--fail-on-breaking", action="store_true", help="breaking finding 이 있으면 exit 1")
    parser.add_argument("--generated-at", help="생성 시각 강제 지정 (ISO 8601, 샘플 재생성용)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    old = load_spec(args.old)
    new = load_spec(args.new)
    findings, body_changes, unresolved = compare_specs(old, new)
    generated_at = args.generated_at or datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    model = build_report_model(
        args.old,
        args.new,
        old,
        new,
        findings,
        body_changes,
        unresolved,
        args.service,
        args.release_version,
        args.clients,
        generated_at,
    )
    report = markdown_report(model)

    output_path = None
    if args.out == "-":
        print(report)
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        output_path = out
        print(str(out))

    if args.json_out:
        render_json(model, args.json_out)

    if not args.no_manifest:
        if args.manifest:
            manifest_path = Path(args.manifest)
        elif output_path is not None:
            manifest_path = output_path.parent / f"{output_path.stem}.artifact.json"
        else:
            manifest_path = None
        if manifest_path is not None:
            outputs = []
            if output_path is not None:
                outputs.append(repo_path(output_path))
            if args.json_out:
                outputs.append(repo_path(args.json_out))
            if args.sources:
                sources = [item.strip() for item in args.sources.split(",") if item.strip()]
            else:
                sources = [repo_path(args.old), repo_path(args.new)]
            primary = (
                repo_path(output_path)
                if output_path is not None
                else (repo_path(args.json_out) if args.json_out else "")
            )
            write_manifest(
                manifest_path,
                primary,
                outputs,
                sources,
                generated_at=generated_at,
            )

    if args.fail_on_breaking and any(
        finding["severity"] == "breaking" for finding in findings
    ):
        return 1
    return 0
