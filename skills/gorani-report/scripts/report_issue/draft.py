"""드래프트 파일 경로와 저장."""

import re
from datetime import datetime
from pathlib import Path


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
