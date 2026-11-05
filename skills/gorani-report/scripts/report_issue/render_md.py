"""이슈 본문 Markdown을 리포트 모델에서 렌더링한다."""

from .constants import AREA_TEXT, KIND_TEXT


def md_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def fence(text, language="text"):
    marker = "```"
    if "```" in text:
        marker = "````"
    return f"{marker}{language}\n{text.rstrip()}\n{marker}"


def environment_table(rows):
    lines = ["## 환경", "", "| 항목 | 값 |", "| --- | --- |"]
    for row in rows:
        lines.append(f"| {md_cell(row['label'])} | {md_cell(row['value'])} |")
    lines.append("")
    return lines


def build_body(meta, values, environment):
    kind = meta["kind"]
    area = meta["area"]
    lines = [
        "## 요약",
        "",
        values["summary"],
        "",
        "## 종류",
        "",
        f"{KIND_TEXT[kind]} (`{kind}`)",
        "",
    ]
    if area:
        lines += ["## 영역", "", AREA_TEXT.get(area, area), ""]
    if kind == "bug":
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
        lines += environment_table(environment)
        if values["error"]:
            lines += ["## 오류 로그", "", fence(values["error"]), ""]
        if values["context"]:
            lines += ["## 추가 맥락", "", values["context"], ""]
    elif kind in {"enhancement", "idea", "format"}:
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
        lines += environment_table(environment)
        if values["error"]:
            lines += ["## 참고 로그", "", fence(values["error"]), ""]
    elif kind == "documentation":
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
        lines += environment_table(environment)
    else:
        if values["proposal"]:
            lines += ["## 질문", "", values["proposal"], ""]
        if values["steps"]:
            lines += ["## 시도한 것", "", values["steps"], ""]
        if values["context"]:
            lines += ["## 참고", "", values["context"], ""]
        lines += environment_table(environment)
    minimum = "재현 가능한 최소 입력만 포함했습니다." if kind == "bug" else "제안에 필요한 최소 정보만 포함했습니다."
    lines += [
        "## 공개 안전 확인",
        "",
        "- [x] 고객 정보·시크릿·내부 URL을 포함하지 않았습니다.",
        f"- [x] {minimum}",
        "- [x] 이 이슈가 공개 저장소에 게시된다는 점을 확인했습니다.",
        "",
        "---",
        "",
        f"이 이슈는 `{values['skill']}` 사용 중 `gorani-report`로 작성했습니다.",
        "",
    ]
    return "\n".join(lines)
