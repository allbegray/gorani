"""입력 릴리스 노트 JSON의 형식과 필수 값을 검사한다."""

from .model import limit_value, safe_href, text


def validate(data, formats):
    errors = []
    warnings = []
    strict_issues = []
    for key, label in (("product", "제품명"), ("version", "버전"), ("release_date", "배포일")):
        if not text(data.get(key)):
            errors.append(f"{label}이(가) 비어 있습니다.")

    highlights = data.get("highlights") or []
    if not isinstance(highlights, list):
        errors.append("highlights는 배열이어야 합니다.")
        highlights = []
    sections = data.get("sections") or []
    if not isinstance(sections, list):
        errors.append("sections는 배열이어야 합니다.")
        sections = []
    item_count = 0
    for index, item in enumerate(highlights, start=1):
        if not isinstance(item, dict):
            errors.append(f"highlights {index}가 객체가 아닙니다.")
            continue
        if not text(item.get("title")):
            errors.append(f"highlights {index}의 title이 비어 있습니다.")
    seen_sections = set()
    for section in sections:
        if not isinstance(section, dict):
            errors.append("sections 항목이 객체가 아닙니다.")
            continue
        name = text(section.get("name"))
        if not name:
            errors.append("sections 항목의 name이 비어 있습니다.")
            continue
        if name in seen_sections:
            strict_issues.append(f"섹션 이름이 중복됩니다: {name}")
        seen_sections.add(name)
        items = section.get("items") or []
        if not isinstance(items, list):
            errors.append(f"'{name}' 섹션의 items가 배열이 아닙니다.")
            continue
        if not items:
            strict_issues.append(f"섹션에 항목이 없습니다: {name}")
        for item in items:
            if not isinstance(item, dict):
                errors.append(f"'{name}' 섹션에 객체가 아닌 항목이 있습니다.")
                continue
            item_count += 1
            if not text(item.get("title")):
                errors.append(f"{name} 섹션에 title이 없는 항목이 있습니다.")
            if not text(item.get("description")):
                errors.append(
                    f"{name} / {text(item.get('title'))} 항목의 description이 비어 있습니다."
                )
            link = text(item.get("link"))
            if link and not safe_href(link):
                strict_issues.append(
                    f"허용되지 않는 링크입니다(https/mailto만 허용): {link}"
                )
    if not highlights and item_count == 0:
        errors.append("highlights 또는 sections items가 하나 이상 필요합니다.")

    breaking = data.get("breaking_changes") or []
    if not isinstance(breaking, list):
        errors.append("breaking_changes는 배열이어야 합니다.")
        breaking = []
    for item in breaking:
        if not isinstance(item, dict):
            errors.append("breaking_changes 항목이 객체가 아닙니다.")
            continue
        if not text(item.get("action")):
            errors.append(
                f"업그레이드 항목 '{text(item.get('title'))}'에 action이 없습니다."
            )
        link = text(item.get("link"))
        if link and not safe_href(link):
            strict_issues.append(
                f"업그레이드 항목에 허용되지 않는 링크가 있습니다: {link}"
            )

    for key, label in (("known_issues", "알려진 문제"), ("upgrade_notes", "업그레이드 참고")):
        value = data.get(key) or []
        if not isinstance(value, list):
            errors.append(f"{label}는 배열이어야 합니다.")
            continue
        for note in value:
            if not text(note):
                warnings.append(f"{label}에 빈 항목이 있습니다.")

    support = data.get("support") or {}
    if not isinstance(support, dict):
        errors.append("support는 객체여야 합니다.")
        support = {}
    support_url = text(support.get("url"))
    support_email = text(support.get("email"))
    if support_url and not safe_href(support_url):
        strict_issues.append(f"지원 URL이 허용되지 않는 형식입니다: {support_url}")
    if support_email and "@" not in support_email:
        strict_issues.append(f"지원 이메일 형식이 아닙니다: {support_email}")
    if not support_url and not support_email:
        strict_issues.append("고객이 문의할 지원 URL 또는 이메일이 없습니다.")

    limits = {
        "short": limit_value(data, "short"),
        "store": limit_value(data, "store"),
    }
    short_summary = text(data.get("short_summary"))
    store_summary = text(data.get("store_summary"))
    if "short" in formats and short_summary and len(short_summary) > limits["short"]:
        errors.append(
            f"short_summary가 {len(short_summary)}자입니다. 제한 {limits['short']}자를 넘습니다."
        )
    if "store" in formats and store_summary and len(store_summary) > limits["store"]:
        errors.append(
            f"store_summary가 {len(store_summary)}자입니다. 제한 {limits['store']}자를 넘습니다."
        )

    commits = data.get("commits") or []
    if not isinstance(commits, list):
        errors.append("commits는 배열이어야 합니다.")
        commits = []
    if not commits:
        strict_issues.append("commit 매핑이 없습니다.")
    for commit in commits:
        if not isinstance(commit, dict):
            strict_issues.append("commit 항목이 객체가 아닙니다.")
            continue
        subject = text(commit.get("subject")) or text(commit.get("short_hash"))
        if commit.get("included", True):
            if not text(commit.get("note")):
                strict_issues.append(f"포함 commit에 note가 없습니다: {subject}")
        elif not text(commit.get("reason")):
            strict_issues.append(f"제외 commit에 reason이 없습니다: {subject}")

    raw_warnings = data.get("warnings") or []
    if not isinstance(raw_warnings, list):
        warnings.append("warnings는 배열이어야 합니다. 무시했습니다.")
    else:
        for warning in raw_warnings:
            warnings.append(text(warning))
    return errors, warnings, strict_issues, limits
