"""gorani-report CLI. 입력 → 리포트 모델 → Markdown/JSON 렌더링을 조정한다."""

import argparse
import os

from .constants import AREA_TEXT, DEFAULT_REPO, KIND_LABELS, MAX_BODY
from .draft import draft_path, write_draft
from .environment import environment_rows, read_skill_metadata
from .github import (
    comment_issue,
    create_issue,
    gh_authenticated,
    gh_available,
    search_duplicates,
)
from .inputs import collect_values
from .model import build_report_model, build_title
from .render_json import render_result, write_model
from .render_md import build_body
from .sanitize import (
    find_risks,
    merge_redactions,
    sanitize,
    sanitize_tools,
    sanitize_values,
)


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
    parser.add_argument("--model-out", default="", help="리포트 모델 JSON을 추가로 저장할 경로")
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


def save_model(args, result, values, environment):
    if not args.model_out:
        return
    model = build_report_model(result, values, environment)
    try:
        write_model(model, args.model_out)
    except OSError as error:
        raise SystemExit(f"리포트 모델을 저장하지 못했습니다: {args.model_out} ({error})")


def main():
    args = parse_args()
    metadata, _ = read_skill_metadata(args.skill)
    args.skill_version = args.skill_version or metadata.get("version", "") or "unknown"
    args.skill_updated = args.skill_updated or metadata.get("updated", "")
    raw = collect_values(args)
    values, redactions = sanitize_values(raw)
    tools, tool_redactions = sanitize_tools(args.tool)
    args.tool = tools
    merge_redactions(redactions, tool_redactions)
    title = build_title(values["summary"], values["skill"])
    environment = environment_rows(args)
    body = build_body({"kind": args.kind, "area": args.area}, values, environment)
    body, body_redactions = sanitize(body)
    merge_redactions(redactions, body_redactions)
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
            save_model(args, result, values, environment)
            if args.json:
                print(render_result(result))
            else:
                print(f"draft: {draft or '-'}")
                print(result["error"])
                print("gh auth login 후 다시 실행하거나, 드래프트를 GitHub 이슈에 붙여넣으세요.")
            return 2
        if risks and not args.force:
            result["error"] = "잔여 위험 패턴이 있어 생성을 중단했습니다: " + ", ".join(risks)
            save_model(args, result, values, environment)
            if args.json:
                print(render_result(result))
            else:
                print(f"draft: {draft or '-'}")
                print(result["error"])
                print("내용을 확인·수정하거나, 안전이 확인된 경우에만 --force를 사용하세요.")
            return 1
        if args.create and duplicates and not args.allow_duplicate:
            result["error"] = "중복 후보가 있어 새 이슈 생성을 중단했습니다."
            save_model(args, result, values, environment)
            if args.json:
                print(render_result(result))
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
            save_model(args, result, values, environment)
            if args.json:
                print(render_result(result))
            else:
                print(f"draft: {draft or '-'}")
                print(f"error: {result['error']}")
            return 1
    save_model(args, result, values, environment)
    if args.json:
        print(render_result(result))
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
