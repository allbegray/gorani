#!/usr/bin/env python3
"""Build a release-check JSON skeleton from a branch or revision range.

Branch mode (default, merge-base):
    python3 compare_revisions.py --mode branch --base origin/main --head origin/develop

Branch mode (tip to tip):
    python3 compare_revisions.py --mode branch --base origin/main --head origin/develop --tip

Revision mode (direct):
    python3 compare_revisions.py --mode revision --from v1.0.0 --to v1.2.0

Revision mode (common ancestor):
    python3 compare_revisions.py --mode revision --from v1.0.0 --to v1.2.0 --merge-base

The output is a release-check input JSON with empty `items`. Fill the
checklist items before running release_xlsx.py.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="릴리스 점검용 diff 컨텍스트 생성")
    parser.add_argument("--mode", choices=["branch", "revision"], default="branch")
    parser.add_argument("--base", default="origin/main", help="branch 모드의 기준 ref")
    parser.add_argument("--head", default="origin/develop", help="branch 모드의 대상 ref")
    parser.add_argument("--from", dest="from_ref", help="revision 모드의 시작 ref")
    parser.add_argument("--to", dest="to_ref", help="revision 모드의 끝 ref")
    parser.add_argument("--tip", action="store_true", help="branch 모드에서 tip 대 tip 비교")
    parser.add_argument("--merge-base", action="store_true", help="revision 모드에서 공통 조상 기준 비교")
    parser.add_argument("--no-fetch", action="store_true", help="fetch 를 실행하지 않음")
    parser.add_argument("--out", default=".qa/release-check-input.json", help="출력 JSON 경로. '-' 이면 stdout")
    parser.add_argument("--project", help="프로젝트명 (기본: 저장소 폴더명)")
    parser.add_argument("--release-version", default="", help="배포 버전")
    return parser.parse_args()


def run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def add_log(logs: list[dict], command: list[str], code: int, note: str = ""):
    logs.append(
        {
            "command": "git " + " ".join(command),
            "exit_code": code,
            "status": "ok" if code == 0 else "failed",
            "note": note,
        }
    )


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        sys.exit("git 저장소가 아닙니다.")
    return Path(result.stdout.strip())


def resolve_ref(repo: Path, ref: str, logs: list[dict]) -> str:
    code, stdout, stderr = run_git(repo, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
    add_log(logs, ["rev-parse", "--verify", f"{ref}^{{commit}}"], code, stderr)
    if code != 0 or not stdout:
        sys.exit(f"ref 를 찾을 수 없습니다: {ref}")
    return stdout.splitlines()[0]


def merge_base(repo: Path, base: str, head: str, logs: list[dict]) -> str:
    code, stdout, stderr = run_git(repo, ["merge-base", base, head])
    add_log(logs, ["merge-base", base, head], code, stderr)
    if code != 0 or not stdout:
        sys.exit(f"공통 조상을 찾을 수 없습니다: {base}, {head}")
    return stdout.splitlines()[0]


def commit_range(args, base_commit: str, head_commit: str) -> str:
    # Commits introduced by head relative to base. Works for both branch and
    # revision modes; merge-base is already reflected in the diff range.
    return f"{base_commit}..{head_commit}"


def diff_range(args, base: str, head: str, merge: str | None) -> str:
    if args.mode == "branch":
        return f"{base}...{head}" if not args.tip else f"{base}..{head}"
    return f"{base}...{head}" if args.merge_base else f"{base}..{head}"


def read_commits(repo: Path, revision_range: str, logs: list[dict]) -> list[dict]:
    fmt = "%h%x09%ad%x09%an%x09%s"
    code, stdout, stderr = run_git(
        repo, ["log", "--no-merges", "--date=short", f"--pretty=format:{fmt}", revision_range]
    )
    add_log(logs, ["log", "--no-merges", "--date=short", revision_range], code, stderr)
    if code != 0:
        sys.exit(f"커밋 로그를 읽을 수 없습니다: {revision_range}")
    commits = []
    for line in stdout.splitlines():
        parts = line.split("\t", 3)
        if len(parts) != 4:
            continue
        commits.append(
            {
                "hash": parts[0],
                "date": parts[1],
                "author": parts[2],
                "subject": parts[3],
            }
        )
    return commits


def read_files(repo: Path, revision_range: str, logs: list[dict]) -> tuple[list[dict], int, int]:
    code, stdout, stderr = run_git(
        repo, ["diff", "--numstat", "--find-renames", revision_range]
    )
    add_log(logs, ["diff", "--numstat", "--find-renames", revision_range], code, stderr)
    if code != 0:
        sys.exit(f"파일 통계를 읽을 수 없습니다: {revision_range}")
    numstat = {}
    additions = deletions = 0
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        add, delete, path = parts[0], parts[1], parts[2]
        try:
            add_n = int(add)
            del_n = int(delete)
        except ValueError:
            add_n = del_n = 0
        numstat[path] = (add_n, del_n)
        additions += add_n
        deletions += del_n

    code, stdout, stderr = run_git(
        repo, ["diff", "--name-status", "--find-renames", revision_range]
    )
    add_log(logs, ["diff", "--name-status", "--find-renames", revision_range], code, stderr)
    if code != 0:
        sys.exit(f"변경 파일 목록을 읽을 수 없습니다: {revision_range}")

    files = []
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        raw_status = parts[0]
        status = raw_status[0]
        if status in {"R", "C"} and len(parts) >= 3:
            old_path, path = parts[1], parts[2]
        else:
            old_path, path = "", parts[1]
        add_n, del_n = numstat.get(path, numstat.get(old_path, (0, 0)))
        entry = {
            "path": path,
            "status": status,
            "additions": add_n,
            "deletions": del_n,
            "area": "",
            "related_items": [],
        }
        if old_path:
            entry["old_path"] = old_path
        files.append(entry)
    return files, additions, deletions


def main() -> int:
    args = parse_args()
    if args.mode == "revision":
        if not args.from_ref or not args.to_ref:
            sys.exit("revision 모드에는 --from 과 --to 가 필요합니다.")
        base_ref, head_ref = args.from_ref, args.to_ref
    else:
        if args.from_ref or args.to_ref:
            sys.exit("branch 모드에서는 --from/--to 대신 --base/--head 를 사용하세요.")
        base_ref, head_ref = args.base, args.head

    repo = repo_root()
    logs: list[dict] = []
    if not args.no_fetch:
        fetch_args = ["fetch", "--tags", "origin"] if args.mode == "revision" else ["fetch", "origin", "--prune"]
        code, _, stderr = run_git(repo, fetch_args)
        add_log(logs, fetch_args, code, stderr)
        if code != 0:
            print(f"warning: fetch 실패: {stderr}", file=sys.stderr)

    base_commit = resolve_ref(repo, base_ref, logs)
    head_commit = resolve_ref(repo, head_ref, logs)
    merge = None
    if (args.mode == "branch" and not args.tip) or (args.mode == "revision" and args.merge_base):
        merge = merge_base(repo, base_commit, head_commit, logs)

    if args.mode == "branch":
        comparison_mode = "branch-tip" if args.tip else "branch-merge-base"
    else:
        comparison_mode = "revision-merge-base" if args.merge_base else "revision"

    commits = read_commits(repo, commit_range(args, base_commit, head_commit), logs)
    files, additions, deletions = read_files(repo, diff_range(args, base_ref, head_ref, merge), logs)

    data = {
        "project": args.project or repo.name,
        "release_version": args.release_version,
        "comparison_mode": comparison_mode,
        "base": base_ref,
        "head": head_ref,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "merge_base": merge or "",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "stats": {
            "commits": len(commits),
            "files": len(files),
            "additions": additions,
            "deletions": deletions,
        },
        "commits": commits,
        "files": files,
        "items": [],
        "logs": logs,
    }

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out == "-":
        print(payload)
    else:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
        print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
