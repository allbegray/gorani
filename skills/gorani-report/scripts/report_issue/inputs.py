"""CLI 인자와 입력 파일을 읽어 리포트 입력값을 만든다."""

from pathlib import Path


def read_text(value, path, label):
    if path:
        try:
            return Path(path).read_text(encoding="utf-8")
        except OSError as error:
            raise SystemExit(f"{label} 파일을 읽지 못했습니다: {path} ({error})")
    return value or ""


def collect_values(args):
    return {
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
