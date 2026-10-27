#!/usr/bin/env python3
"""git 범위에서 고객 릴리스 노트 후보를 수집한다.

입력: git 저장소, 이전 릴리스..대상 범위
출력: release-input.json (notes_build.py 입력의 초안)
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

SECTION_BY_CATEGORY = {
    "feature": "새 기능",
    "improvement": "개선",
    "fix": "수정",
    "security": "보안",
    "internal": "제외",
    "other": "기타",
}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$"
)
BREAKING_RE = re.compile(r"(?im)^\s*breaking[ -]change\s*:")
SECURITY_RE = re.compile(
    r"\bsecurity\b|\bcve-\d{4}-\d+\b|\bvulnerab|\bxss\b|\bcsrf\b|보안|취약", re.I
)
INTERNAL_RE = re.compile(
    r"\b(chore|docs?|readme|tests?|ci|build|lint|format|typo|bump|deps?|dependenc\w*|"
    r"lockfile|release|version)\b|문서|테스트|빌드|의존성|버전|오타",
    re.I,
)
FEATURE_RE = re.compile(
    r"\b(add|added|implement\w*|support\w*|introduce\w*|new)\b|추가|지원|도입|신규", re.I
)
FIX_RE = re.compile(
    r"\b(fix|fixed|bug|resolve\w*|correct\w*|crash\w*|error)\b|수정|고침|해결", re.I
)
IMPROVEMENT_RE = re.compile(
    r"\b(improve\w*|enhance\w*|optimiz\w*|performance|faster|speed)\b|개선|최적화|성능|향상",
    re.I,
)
REFERENCE_RE = re.compile(r"#\d+|\b[A-Z][A-Z0-9]+-\d+\b")
TAG_RE = re.compile(r"^v?(\d+\.\d+\.\d+(?:[-+].+)?)$")


def parse_args():
    parser = argparse.ArgumentParser(description="릴리스 노트 후보 수집")
    parser.add_argument("--repo", default=".", help="git 저장소 경로 (기본: 현재 디렉터리)")
    parser.add_argument("--from", dest="from_ref", help="이전 릴리스 (기본: 대상의 최신 태그)")
    parser.add_argument("--to", dest="to_ref", default="HEAD", help="대상 (기본: HEAD)")
    parser.add_argument("--product", help="제품명 (기본: package.json/pyproject/Cargo.toml)")
    parser.add_argument("--version", help="릴리스 버전 (기본: 대상 태그 또는 package.json)")
    parser.add_argument("--date", help="릴리스 날짜 (기본: 오늘)")
    parser.add_argument("--language", default="ko", help="고객 문구 언어 코드 (기본: ko)")
    parser.add_argument("--out", default=".release/release-input.json", help="출력 JSON 경로")
    parser.add_argument("--max-commits", type=int, default=500, help="최대 commit 수 (기본: 500)")
    parser.add_argument("--generated-at", help="생성 시각 강제 지정 (ISO 8601, 샘플 재생성용)")
    return parser.parse_args()


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )


def resolve_commit(repo, ref, label):
    result = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if result.returncode != 0:
        sys.exit(f"{label}을(를) 확인할 수 없습니다: {ref}")
    return result.stdout.strip()


def guess_product(repo):
    package_json = repo / "package.json"
    if package_json.is_file():
        try:
            value = json.loads(package_json.read_text(encoding="utf-8")).get("name")
            if value:
                return str(value).strip()
        except (OSError, json.JSONDecodeError):
            pass
    for filename, section in (("pyproject.toml", "project"), ("Cargo.toml", "package")):
        path = repo / filename
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(
            rf"(?ms)^\[{section}\].*?^name\s*=\s*\"([^\"]+)\"", text
        )
        if match:
            return match.group(1).strip()
    return repo.name


def guess_version(repo, to_ref, explicit):
    if explicit:
        return explicit.strip().lstrip("v")
    match = TAG_RE.match(to_ref.strip())
    if match:
        return match.group(1)
    package_json = repo / "package.json"
    if package_json.is_file():
        try:
            value = json.loads(package_json.read_text(encoding="utf-8")).get("version")
            if value:
                return str(value).strip()
        except (OSError, json.JSONDecodeError):
            pass
    return ""


def classify(subject, body):
    text = f"{subject}\n{body}"
    lower = subject.lower()
    match = CONVENTIONAL_RE.match(subject.strip())
    breaking = bool(BREAKING_RE.search(body)) or bool(re.search(r"(?i)^breaking\b", subject))
    category = "other"
    confidence = "low"
    reason = ""
    if match:
        breaking = breaking or bool(match.group("breaking"))
        commit_type = match.group("type").lower()
        if commit_type == "feat":
            category, confidence = "feature", "high"
        elif commit_type == "fix":
            category, confidence = "fix", "high"
        elif commit_type == "perf":
            category, confidence = "improvement", "high"
        elif commit_type == "security":
            category, confidence = "security", "high"
        elif commit_type in ("docs", "test", "build", "ci", "chore", "style"):
            category, confidence = "internal", "high"
            reason = f"내부 변경({commit_type})"
        elif commit_type == "refactor":
            category, confidence = "internal", "medium"
            reason = "리팩터링, 사용자 영향 확인 필요"
        elif commit_type == "revert":
            category, confidence = "other", "low"
    if not match or category == "other":
        if SECURITY_RE.search(lower):
            category, confidence = "security", "medium"
        elif INTERNAL_RE.search(lower):
            category, confidence = "internal", "medium"
            reason = "내부 변경 키워드"
        elif FEATURE_RE.search(lower):
            category, confidence = "feature", "medium"
        elif FIX_RE.search(lower):
            category, confidence = "fix", "medium"
        elif IMPROVEMENT_RE.search(lower):
            category, confidence = "improvement", "medium"
    included = category != "internal" or breaking
    return {
        "suggested_category": category,
        "suggested_section": "업그레이드 전 확인" if breaking else SECTION_BY_CATEGORY[category],
        "confidence": confidence,
        "breaking": breaking,
        "included": included,
        "reason": "" if included else reason or "내부 변경",
    }


def main():
    args = parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        check = git(repo, "rev-parse", "--show-toplevel")
        if check.returncode != 0:
            sys.exit(f"git 저장소가 아닙니다: {repo}")

    to_label = args.to_ref or "HEAD"
    to_sha = resolve_commit(repo, to_label, "대상")
    if args.from_ref:
        from_label = args.from_ref
    else:
        described = git(repo, "describe", "--tags", "--abbrev=0", to_sha)
        if described.returncode != 0 or not described.stdout.strip():
            sys.exit(
                "이전 릴리스 태그를 찾지 못했습니다. --from 으로 시작 지점을 지정하세요."
            )
        from_label = described.stdout.strip()
    from_sha = resolve_commit(repo, from_label, "시작 지점")
    if from_sha == to_sha:
        sys.exit("변경 commit이 없습니다. --from 과 --to 를 확인하세요.")

    range_label = f"{from_sha}..{to_sha}"
    count_result = git(repo, "rev-list", "--count", "--no-merges", range_label)
    total = int(count_result.stdout.strip() or "0")
    if total == 0:
        sys.exit("변경 commit이 없습니다. merge commit 만 있는 범위인지 확인하세요.")
    if total > args.max_commits:
        sys.exit(
            f"commit 이 {total}개입니다. --max-commits({args.max_commits})를 늘리거나 "
            "릴리스 범위를 좁히세요."
        )
    merge_result = git(repo, "rev-list", "--count", "--merges", range_label)
    merge_count = int(merge_result.stdout.strip() or "0")

    log_result = git(
        repo,
        "log",
        "--no-merges",
        "--date=short",
        "--pretty=format:%H%x1f%ad%x1f%an%x1f%s%x1f%b%x1e",
        range_label,
    )
    if log_result.returncode != 0:
        sys.exit(f"git log 실패: {log_result.stderr.strip()}")

    warnings = []
    if merge_count:
        warnings.append(f"merge commit {merge_count}개는 목록에서 제외했습니다.")
    commits = []
    for record in log_result.stdout.split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        fields = record.split("\x1f", 4)
        if len(fields) < 4:
            warnings.append("형식을 해석하지 못한 commit 1개를 건너뛰었습니다.")
            continue
        sha, committed, author, subject = fields[:4]
        body = fields[4].strip() if len(fields) > 4 else ""
        if not subject.strip():
            continue

        files_result = git(
            repo, "show", "--name-only", "--format=", "--no-renames", sha
        )
        files = [
            line.strip()
            for line in files_result.stdout.splitlines()
            if line.strip()
        ]
        file_count = len(files)
        files = files[:30]
        if file_count > len(files):
            warnings.append(
                f"{sha[:7]}의 변경 파일 {file_count}개 중 {len(files)}개만 기록했습니다."
            )

        suggestion = classify(subject, body)
        commits.append(
            {
                "hash": sha,
                "short_hash": sha[:7],
                "date": committed,
                "author": author,
                "subject": subject.strip(),
                "body": body[:4000],
                "files": files,
                "file_count": file_count,
                "references": sorted(set(REFERENCE_RE.findall(f"{subject}\n{body}"))),
                **suggestion,
                "note": "",
            }
        )

    if not commits:
        sys.exit("수집된 commit이 없습니다.")
    if any(not commit["subject"] for commit in commits):
        warnings.append("subject 가 비어 있는 commit 이 있습니다.")
    uncertain = [
        commit for commit in commits if commit["confidence"] == "low"
    ]
    if uncertain:
        warnings.append(
            f"분류가 불확실한 commit {len(uncertain)}개가 있습니다. "
            "subject와 diff를 보고 직접 분류하세요."
        )

    product = (args.product or guess_product(repo)).strip()
    version = guess_version(repo, to_label, args.version)
    if not product:
        warnings.append("제품명이 비어 있습니다. --product 로 지정하세요.")
    if not version:
        warnings.append("버전이 비어 있습니다. --version 으로 지정하세요.")

    generated_at = args.generated_at or datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    output = {
        "product": product,
        "version": version,
        "release_date": args.date or date.today().isoformat(),
        "language": args.language,
        "audience": "고객",
        "generated_at": generated_at,
        "range": {
            "from": from_label,
            "to": to_label,
            "from_commit": from_sha,
            "to_commit": to_sha,
        },
        "highlights": [],
        "summary": "",
        "sections": [],
        "breaking_changes": [],
        "known_issues": [],
        "upgrade_notes": [],
        "support": {"url": "", "email": ""},
        "short_summary": "",
        "store_summary": "",
        "limits": {"short": 500, "store": 4000},
        "commits": commits,
        "warnings": warnings,
        "logs": [
            {
                "tool": "git",
                "command": f"git log --no-merges --date=short {from_label}..{to_label}",
                "status": "ok",
                "note": f"commits {len(commits)}, merges excluded {merge_count}",
            }
        ],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    categories = {}
    for commit in commits:
        key = commit["suggested_category"]
        categories[key] = categories.get(key, 0) + 1
    print(
        json.dumps(
            {
                "output": str(out_path),
                "range": f"{from_label}..{to_label}",
                "commits": len(commits),
                "included": sum(1 for commit in commits if commit["included"]),
                "excluded": sum(1 for commit in commits if not commit["included"]),
                "categories": categories,
                "warnings": warnings,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
