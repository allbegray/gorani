"""라이선스 표현을 정규화하고 고지 의무를 분류한다."""

from .constants import ALIASES, POLICY, RANK


def canonical_license(value):
    text = (value or "").strip()
    if not text:
        return ""
    key = text.lower()
    if key in ALIASES:
        return ALIASES[key]
    if text in POLICY:
        return text
    for name in POLICY:
        if name.lower() == key:
            return name
    return text


def classify_single(value):
    return POLICY.get(canonical_license(value), "unknown")


def strip_outer_parens(expression):
    if not (expression.startswith("(") and expression.endswith(")")):
        return expression
    depth = 0
    for index, char in enumerate(expression):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0 and index != len(expression) - 1:
                return expression
    return expression[1:-1].strip() if depth == 0 else expression


def split_top_level(expression, operator):
    parts = []
    depth = 0
    start = 0
    index = 0
    upper = expression.upper()
    while index < len(expression):
        char = expression[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and upper.startswith(operator, index):
            before_ok = index == 0 or expression[index - 1].isspace()
            after = index + len(operator)
            after_ok = after >= len(expression) or expression[after].isspace()
            if before_ok and after_ok:
                parts.append(expression[start:index].strip())
                start = after
                index = after
                continue
        index += 1
    if parts:
        parts.append(expression[start:].strip())
    return parts


def classify(value):
    expression = (value or "").strip()
    if not expression:
        return "unknown"
    stripped = strip_outer_parens(expression)
    if stripped != expression:
        return classify(stripped)
    or_parts = split_top_level(expression, "OR")
    if len(or_parts) > 1:
        statuses = [classify(part) for part in or_parts]
        if "unknown" not in statuses:
            return min(statuses, key=lambda item: RANK[item])
    and_parts = split_top_level(expression, "AND")
    if len(and_parts) > 1:
        statuses = [classify(part) for part in and_parts]
        if "unknown" not in statuses:
            return max(statuses, key=lambda item: RANK[item])
    return classify_single(expression)
