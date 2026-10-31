#!/usr/bin/env python3
"""gorani 스킬 오류·개선점을 GitHub 이슈로 정리한다.

기본은 드래프트 생성이다. `--create` 또는 `--comment-on`을 줘야 실제로
GitHub에 쓴다. 본문은 만들기 전에 홈 경로·토큰·비밀번호·이메일·내부 URL을
마스킹하고, 남은 위험 패턴이 있으면 `--force` 없이는 생성하지 않는다.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

DEFAULT_REPO = "allbegray/gorani"
KIND_LABELS = {
    "bug": "bug",
    "enhancement": "enhancement",
    "idea": "enhancement",
    "format": "enhancement",
    "documentation": "documentation",
    "question": "question",
}
KIND_TEXT = {
    "bug": "오류",
    "enhancement": "개선",
    "idea": "아이디어",
    "format": "양식",
    "documentation": "문서",
    "question": "질문",
}
AREA_TEXT = {
    "excel": "Excel",
    "markdown": "Markdown",
    "html": "HTML",
    "cli": "CLI",
    "docs": "문서",
    "other": "기타",
}
MAX_LOG = 20000
MAX_BODY = 60000
RISK_PATTERNS = [
    ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("token", r"(?i)\b(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_|sk-|AKIA|xox[baprs]-)"),
    ("credential URL", r"(?i)(?:postgres(?:ql)?|mysql|mongodb|redis)://[^/\s:@]+:(?!<redacted>)[^/\s@]+@"),
    ("password", r"(?i)(?:password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*(?!<redacted>)\S+"),
    ("email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("internal URL", r"(?i)https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="gorani 스킬 오류·개선·아이디어·양식 제안을 GitHub 이슈로 정리")
    parser.add_argument("--skill", required=True, help="대상 스킬 이름. 예: gorani-table-spec")
    parser.add_argument("--kind", choices=sorted(KIND_LABELS), default="bug", help="이슈 종류: bug, enhancement, idea, format, documentation, question (기본: bug)")
    parser.add_argument("--area", choices=sorted(AREA_TEXT), default="", help="제안 영역: excel, markdown, html, cli, docs, other")
    parser.add_argument("--summary", required=True, help="한 줄 요약")
    parser.add_argument("--expected", default="", help="기대한 결과")
    parser.add_argument("--actual", default="", help="실제로 일어난 일. 아이디어·양식에서는 현재 동작으로도 사용")
    parser.add_argument("--proposal", default="", help="제안 내용. 개선·아이디어·양식·문서")
    parser.add_argument("--proposal-file", help="제안 내용 파일")
    parser.add_argument("--benefit", default="", help="기대 효과")
    parser.add_argument("--benefit-file", help="기대 효과 파일")
    parser.add_argument("--current", default="", help="현재 동작·양식")
    parser.add_argument("--current-file", help="현재 동작·양식 파일")
    parser.add_argument("--steps", default="", help="재현 절차")
    parser.add_argument("--steps-file", help="재현 절차 파일")
    parser.add_argument("--command", default="", help="실행한 명령. 민감 정보는 자동 마스킹")
    parser.add_argument("--error", default="", help="오류 메시지·스택 트레이스")
    parser.add_argument("--error-file", help="오류 로그 파일")
    parser.add_argument("--context", default="", help="추가 맥락")
    parser.add_argument("--context-file", help="추가 맥락 파일")
    parser.add_argument("--tool", action="append", default=[], help="도구 버전. 예: openpyxl=3.1.5 (반복 가능)")
    parser.add_argument("--skill-version", default="", help="스킬 버전 override. 기본은 SKILL.md metadata.version")
    parser.add_argument("--skill-updated", default="", help="스킬 갱신일 override. 기본은 SKILL.md metadata.updated")
    parser.add_argument(
        "--repo",
        default=os.environ.get("GORANI_REPORT_REPO", DEFAULT_REPO),
        help=f"이슈를 만들 저장소 (기본: {DEFAULT_REPO})",
    )
    parser.add_argument("--out", default="", help="드래프트 경로. '-'이면 파일을 만들지 않음")
    parser.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    parser.add_argument("--create", action="store_true", help="사용자 확인 후 실제 이슈 생성")
    parser.add_argument("--comment-on", type=int, help="새 이슈 대신 기존 이슈 번호에 코멘트")
    parser.add_argument("--allow-duplicate", action="store_true", help="중복 후보가 있어도 새 이슈 생성")
    parser.add_argument("--no-duplicate-search", action="store_true", help="중복 검색 생략")
    parser.add_argument("--force", action="store_true", help="잔여 위험 패턴이 있어도 생성")
    args = parser.parse_args()
    if args.create and args.comment_on:
        parser.error("--create 와 --comment-on 은 함께 쓸 수 없습니다.")
    return args


def read_text(value, path, label):
    if path:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError as error:
            raise SystemExit(f"{label} 파일을 읽지 못했습니다: {path} ({error})")
    return value or ""


def clip(text):
    if len(text) <= MAX_LOG:
        return text
    half = MAX_LOG // 2
    return text[:half] + "\n... (중략) ...\n" + text[-half:]


def sanitize(text):
    redactions = {}

    def sub(label, pattern, repl, flags=0):
        nonlocal text
        text, count = re.subn(pattern, repl, text, flags=flags)
        if count:
            redactions[label] = redactions.get(label, 0) + count

    cwd = str(Path.cwd())
    if cwd and cwd != "/":
        sub("cwd", re.escape(cwd), ".")
    home = str(Path.home())
    if home and home != "/":
        sub("home", re.escape(home), "~")
    sub("home", r"/Users/[^/\s]+", "~")
    sub("home", r"/home/[^/\s]+", "~")
    sub("home", r"C:\\Users\\[^\\\s]+", "~")
    sub("token", r"(?i)\b(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]+", "<redacted-token>")
    sub("token", r"(?i)\bsk-[A-Za-z0-9_-]{16,}", "<redacted-token>")
    sub("token", r"\bAKIA[0-9A-Z]{16}\b", "<redacted-token>")
    sub("token", r"\bxox[baprs]-[A-Za-z0-9-]+", "<redacted-token>")
    sub("jwt", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "<redacted-token>")
    sub(
        "private-key",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        "<redacted-private-key>",
        re.S,
    )
    sub(
        "credential",
        r"(?i)((?:postgres(?:ql)?|mysql|mongodb|redis)://[^/\s:@]+:)([^/\s@]+)(@)",
        r"\1<redacted>\3",
    )
    sub(
        "credential",
        r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?([^\s,;]+)",
        r"\1<redacted>",
    )
    sub("credential", r"(?i)(\bbearer\s+)([A-Za-z0-9._~+/=-]{10,})", r"\1<redacted>")
    sub(
        "credential",
        r"(?i)((?:password|passwd|pwd|secret|token|api[_-]?key|bearer)\s*[:=]\s*)([^\s,;]+)",
        r"\1<redacted>",
    )
    sub("credential", r"(?i)(aws_secret_access_key\s*[:=]\s*)(\S+)", r"\1<redacted>")
    sub(
        "internal-url",
        r"(?i)https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)[^\s)\]]*",
        "<internal-url>",
    )
    sub("email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<email>")
    return text, redactions


def find_risks(text):
    findings = []
    for label, pattern in RISK_PATTERNS:
        if re.search(pattern, text):
            findings.append(label)
    return findings


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as error:
        return None, str(error)
    return result, ""


def gh_available():
    return shutil.which("gh") is not None


def gh_authenticated():
    if not gh_available():
        return False, "gh 없음"
    result, error = run_command(["gh", "auth", "status"])
    if result is None:
        return False, error
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip() or "gh 인증 필요"
    return True, ""


def search_duplicates(repo, skill):
    result, error = run_command(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--search",
            skill,
            "--limit",
            "10",
            "--json",
            "number,title,url,state",
        ]
    )
    if result is None:
        return [], error
    if result.returncode != 0:
        return [], (result.stderr or result.stdout).strip() or "중복 검색 실패"
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return [], f"중복 검색 JSON 파싱 실패: {error}"
    if not isinstance(data, list):
        return [], "중복 검색 결과 형식이 올바르지 않습니다."
    return data, ""


def git_value(root, *args):
    result, _ = run_command(["git", "-C", str(root), *args])
    if result is None or result.returncode != 0:
        return ""
    return result.stdout.strip()


def skill_repo_root():
    return Path(__file__).resolve().parents[3]


def skill_candidates(skill):
    roots = [
        Path.cwd() / ".opencode" / "skills",
        Path.cwd() / ".claude" / "skills",
        Path.cwd() / ".agents" / "skills",
        Path.cwd() / "skills",
        Path.home() / ".config" / "opencode" / "skills",
        Path.home() / ".claude" / "skills",
        Path.home() / ".agents" / "skills",
        skill_repo_root() / "skills",
    ]
    seen = set()
    for root in roots:
        path = root / skill / "SKILL.md"
        if path in seen:
            continue
        seen.add(path)
        yield path


def read_skill_metadata(skill):
    for path in skill_candidates(skill):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not match:
            continue
        metadata = {}
        in_metadata = False
        for line in match.group(1).splitlines():
            if line.strip() == "metadata:":
                in_metadata = True
                continue
            if in_metadata:
                if line.startswith("  ") and ":" in line:
                    key, value = line.strip().split(":", 1)
                    metadata[key.strip()] = value.strip().strip('"').strip("'")
                elif line and not line.startswith(" "):
                    in_metadata = False
        return metadata, path
    return {}, None


def environment_rows(args):
    root = skill_repo_root()
    commit = git_value(root, "rev-parse", "--short", "HEAD") or "unknown"
    dirty = bool(git_value(root, "status", "--porcelain"))
    shell = Path(os.environ.get("SHELL", "")).name or "unknown"
    rows = [
        ("스킬", args.skill),
        ("스킬 버전", args.skill_version),
    ]
    if args.skill_updated:
        rows.append(("스킬 갱신일", args.skill_updated))
    rows += [
        ("skill source commit", commit + ("+dirty" if dirty else "")),
        ("OS", platform.platform()),
        ("Python", sys.version.split()[0]),
        ("Shell", shell),
    ]
    if args.tool:
        rows.append(("도구", "\n".join(args.tool)))
    return rows


def md_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def fence(text, language="text"):
    marker = "```"
    if "```" in text:
        marker = "````"
    return f"{marker}{language}\n{text.rstrip()}\n{marker}"


def build_body(args, values):
    skill = values["skill"]
    rows = environment_rows(args)
    lines = [
        "## 요약",
        "",
        values["summary"],
        "",
        "## 종류",
        "",
        f"{KIND_TEXT[args.kind]} (`{args.kind}`)",
        "",
    ]
    if args.area:
        lines += ["## 영역", "", AREA_TEXT.get(args.area, args.area), ""]
    if args.kind == "bug":
        if values["steps"]:
            lines += ["## 재현 절차", "", values["steps"], ""]
        if values["expected"]:
            lines += ["## 기대 결과", "", values["expected"], ""]
        if values["actual"]:
            lines += ["## 실제 결과", "", values["actual"], ""]
        if values["proposal"]:
            lines += ["## 추가 제안", "", values["proposal"], ""]
        if values["benefit"]:
            lines += ["## 기대 효과", "", values["benefit"], ""]
        if values["command"]:
            lines += ["## 실행 명령", "", fence(values["command"], "bash"), ""]
        lines += environment_table(rows)
        if values["error"]:
            lines += ["## 오류 로그", "", fence(values["error"]), ""]
        if values["context"]:
            lines += ["## 추가 맥락", "", values["context"], ""]
    elif args.kind in {"enhancement", "idea", "format"}:
        proposal = values["proposal"] or values["expected"]
        benefit = values["benefit"] or values["context"]
        current = values["current"] or values["actual"]
        if proposal:
            lines += ["## 제안", "", proposal, ""]
        if benefit:
            lines += ["## 기대 효과", "", benefit, ""]
        if current:
            lines += ["## 현재 동작·양식", "", current, ""]
        if values["steps"]:
            lines += ["## 참고한 화면·명령", "", values["steps"], ""]
        if values["command"]:
            lines += ["## 실행 명령", "", fence(values["command"], "bash"), ""]
        lines += environment_table(rows)
        if values["error"]:
            lines += ["## 참고 로그", "", fence(values["error"]), ""]
    elif args.kind == "documentation":
        proposal = values["proposal"] or values["expected"]
        current = values["current"] or values["actual"]
        if proposal:
            lines += ["## 제안", "", proposal, ""]
        if current:
            lines += ["## 현재 문서", "", current, ""]
        if values["benefit"]:
            lines += ["## 기대 효과", "", values["benefit"], ""]
        if values["context"]:
            lines += ["## 참고", "", values["context"], ""]
        lines += environment_table(rows)
    else:
        if values["proposal"]:
            lines += ["## 질문", "", values["proposal"], ""]
        if values["steps"]:
            lines += ["## 시도한 것", "", values["steps"], ""]
        if values["context"]:
            lines += ["## 참고", "", values["context"], ""]
        lines += environment_table(rows)
    minimum = "재현 가능한 최소 입력만 포함했습니다." if args.kind == "bug" else "제안에 필요한 최소 정보만 포함했습니다."
    lines += [
        "## 공개 안전 확인",
        "",
        "- [x] 고객 정보·시크릿·내부 URL을 포함하지 않았습니다.",
        f"- [x] {minimum}",
        "- [x] 이 이슈가 공개 저장소에 게시된다는 점을 확인했습니다.",
        "",
        "---",
        "",
        f"이 이슈는 `{skill}` 사용 중 `gorani-report`로 작성했습니다.",
        "",
    ]
    return "\n".join(lines)


def environment_table(rows):
    lines = ["## 환경", "", "| 항목 | 값 |", "| --- | --- |"]
    for label, value in rows:
        lines.append(f"| {md_cell(label)} | {md_cell(value)} |")
    lines.append("")
    return lines


def draft_path(args):
    if args.out == "-":
        return None
    if args.out:
        return Path(args.out)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_skill = re.sub(r"[^A-Za-z0-9._-]+", "-", args.skill).strip("-") or "skill"
    return Path(".gorani") / "report" / f"{safe_skill}-{stamp}.md"


def write_draft(path, body):
    if path is None:
        return ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def write_temp_body(body):
    handle, path = tempfile.mkstemp(prefix="gorani-report-", suffix=".md")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(body)
    return path


def create_issue(repo, title, body, label):
    path = write_temp_body(body)
    try:
        command = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", path]
        if label:
            command += ["--label", label]
        result, error = run_command(command)
    finally:
        Path(path).unlink(missing_ok=True)
    if result is None:
        return False, error
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip() or "이슈 생성 실패"
    return True, result.stdout.strip()


def comment_issue(repo, number, body):
    path = write_temp_body(body)
    try:
        result, error = run_command(
            ["gh", "issue", "comment", str(number), "--repo", repo, "--body-file", path]
        )
    finally:
        Path(path).unlink(missing_ok=True)
    if result is None:
        return False, error
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip() or "코멘트 생성 실패"
    return True, result.stdout.strip()


def main():
    args = parse_args()
    metadata, _ = read_skill_metadata(args.skill)
    args.skill_version = args.skill_version or metadata.get("version", "") or "unknown"
    args.skill_updated = args.skill_updated or metadata.get("updated", "")
    raw = {
        "skill": args.skill,
        "summary": args.summary,
        "steps": read_text(args.steps, args.steps_file, "재현 절차"),
        "expected": read_text(args.expected, None, "기대 결과"),
        "actual": read_text(args.actual, None, "실제 결과"),
        "proposal": read_text(args.proposal, args.proposal_file, "제안"),
        "benefit": read_text(args.benefit, args.benefit_file, "기대 효과"),
        "current": read_text(args.current, args.current_file, "현재 동작·양식"),
        "command": args.command,
        "error": read_text(args.error, args.error_file, "오류 로그"),
        "context": read_text(args.context, args.context_file, "추가 맥락"),
    }
    clipped = {}
    redactions = {}
    for key, value in raw.items():
        clean, counts = sanitize(value)
        clipped[key] = clip(clean)
        for label, count in counts.items():
            redactions[label] = redactions.get(label, 0) + count
    tools = []
    for item in args.tool:
        clean, counts = sanitize(item)
        tools.append(clean)
        for label, count in counts.items():
            redactions[label] = redactions.get(label, 0) + count
    args.tool = tools
    title = clipped["summary"]
    title = re.sub(r"\s+", " ", title).strip()
    if len(title) > 180:
        title = title[:177].rstrip() + "..."
    title = f"[{clipped['skill']}] {title}"
    body = build_body(args, clipped)
    body, body_redactions = sanitize(body)
    for rule, count in body_redactions.items():
        redactions[rule] = redactions.get(rule, 0) + count
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY].rstrip() + "\n\n... (본문 길이 제한으로 중략) ...\n"
    risks = find_risks(body)
    path = draft_path(args)
    draft = "-" if path is None else write_draft(path, body)
    label = KIND_LABELS[args.kind]
    duplicates = []
    duplicate_error = ""
    if not args.no_duplicate_search:
        if not gh_available():
            duplicate_error = "gh 없음"
        else:
            available, auth_error = gh_authenticated()
            if not available:
                duplicate_error = auth_error
            else:
                duplicates, duplicate_error = search_duplicates(args.repo, args.skill)
    authenticated, auth_error = (False, "gh 없음")
    if gh_available():
        authenticated, auth_error = gh_authenticated()
    action = args.create or args.comment_on is not None
    result = {
        "repo": args.repo,
        "skill": args.skill,
        "skill_version": args.skill_version,
        "skill_updated": args.skill_updated,
        "kind": args.kind,
        "area": args.area,
        "title": title,
        "label": label,
        "draft": draft,
        "body": body,
        "duplicates": duplicates,
        "duplicate_error": duplicate_error,
        "redactions": redactions,
        "risks": risks,
        "authenticated": authenticated,
        "auth_error": auth_error,
        "created": False,
        "commented": False,
        "url": "",
        "error": "",
    }
    if action:
        if not authenticated:
            if not gh_available():
                result["error"] = "gh가 설치되어 있지 않습니다. gh를 설치한 뒤 `gh auth login`을 실행하세요."
            else:
                result["error"] = f"gh 인증이 필요합니다: {auth_error}"
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"draft: {draft or '-'}")
                print(result["error"])
                print("gh auth login 후 다시 실행하거나, 드래프트를 GitHub 이슈에 붙여넣으세요.")
            return 2
        if risks and not args.force:
            result["error"] = "잔여 위험 패턴이 있어 생성을 중단했습니다: " + ", ".join(risks)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"draft: {draft or '-'}")
                print(result["error"])
                print("내용을 확인·수정하거나, 안전이 확인된 경우에만 --force를 사용하세요.")
            return 1
        if args.create and duplicates and not args.allow_duplicate:
            result["error"] = "중복 후보가 있어 새 이슈 생성을 중단했습니다."
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"draft: {draft or '-'}")
                for item in duplicates:
                    print(f"  #{item.get('number')} {item.get('title')} ({item.get('state', '')}) {item.get('url', '')}")
                print(result["error"])
                print("기존 이슈에 코멘트하려면 --comment-on <번호>, 새 이슈를 만들려면 --allow-duplicate를 사용하세요.")
            return 1
        if args.create:
            ok, output = create_issue(args.repo, title, body, label)
            result["created"] = ok
            result["url"] = output if ok else ""
            result["error"] = "" if ok else output
        else:
            ok, output = comment_issue(args.repo, args.comment_on, body)
            result["commented"] = ok
            result["url"] = output if ok else ""
            result["error"] = "" if ok else output
        if not ok:
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"draft: {draft or '-'}")
                print(f"error: {result['error']}")
            return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    print(f"draft: {draft or '-'}")
    if result["error"]:
        print(f"error: {result['error']}")
    if redactions:
        summary = ", ".join(f"{key}={value}" for key, value in sorted(redactions.items()))
        print(f"redactions: {summary}")
    if risks:
        print("risk: " + ", ".join(risks))
    if duplicates:
        print(f"duplicates: {len(duplicates)}")
        for item in duplicates:
            print(f"  #{item.get('number')} {item.get('title')} ({item.get('state', '')}) {item.get('url', '')}")
    elif duplicate_error:
        print(f"duplicates: 확인하지 못함 ({duplicate_error})")
    else:
        print("duplicates: 없음")
    if result["created"] or result["commented"]:
        print(f"url: {result['url']}")
    print("---")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
