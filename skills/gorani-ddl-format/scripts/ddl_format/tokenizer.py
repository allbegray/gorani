"""SQL 문장 분리와 토큰 유틸.

dump 파일은 문자열 리터럴·달러 인용·주석·괄호가 섞여 있어 단순 split(';')로는
나눌 수 없다. 이 모듈은 그 경계를 지키면서 문장과 항목을 나눈다.
"""


class Token:
    __slots__ = ("kind", "text", "upper")

    def __init__(self, kind, text):
        self.kind = kind
        self.text = text
        self.upper = text.upper()

    def __repr__(self):
        return f"Token({self.kind!r}, {self.text!r})"


PUNCT_PAIRS = (">=", "<=", "<>", "!=", "||", "::", ":=", "->>", "->", "#>", "#>>")


def split_statements(text):
    """주석을 걷어내며 최상위 `;`에서 문장을 나눈다.

    반환 항목: {"sql": str, "line": int}. 빈 문장은 버린다.
    """
    statements = []
    buffer = []
    start_line = 1
    line = 1
    index = 0
    length = len(text)
    depth = 0
    state = None  # line_comment, block_comment, single, double, backtick, dollar
    dollar_tag = ""

    while index < length:
        char = text[index]

        if state == "line_comment":
            if char == "\n":
                state = None
                buffer.append(char)
                line += 1
            index += 1
            continue

        if state == "block_comment":
            if text.startswith("*/", index):
                state = None
                index += 2
                continue
            if char == "\n":
                buffer.append(char)
                line += 1
            index += 1
            continue

        if state == "single":
            buffer.append(char)
            if char == "\\" and index + 1 < length:
                buffer.append(text[index + 1])
                index += 2
                continue
            if char == "'":
                if index + 1 < length and text[index + 1] == "'":
                    buffer.append("'")
                    index += 2
                    continue
                state = None
            if char == "\n":
                line += 1
            index += 1
            continue

        if state in ("double", "backtick"):
            buffer.append(char)
            closer = '"' if state == "double" else "`"
            if char == closer:
                if index + 1 < length and text[index + 1] == closer:
                    buffer.append(closer)
                    index += 2
                    continue
                state = None
            if char == "\n":
                line += 1
            index += 1
            continue

        if state == "dollar":
            if text.startswith(dollar_tag, index):
                buffer.append(dollar_tag)
                index += len(dollar_tag)
                state = None
                continue
            buffer.append(char)
            if char == "\n":
                line += 1
            index += 1
            continue

        if char == "-" and text.startswith("--", index):
            state = "line_comment"
            index += 2
            continue

        if char == "/" and text.startswith("/*", index):
            state = "block_comment"
            index += 2
            continue

        if char == "'":
            state = "single"
            buffer.append(char)
            index += 1
            continue

        if char == '"':
            state = "double"
            buffer.append(char)
            index += 1
            continue

        if char == "`":
            state = "backtick"
            buffer.append(char)
            index += 1
            continue

        if char == "$":
            tag = dollar_tag_at(text, index)
            if tag:
                state = "dollar"
                dollar_tag = tag
                buffer.append(tag)
                index += len(tag)
                continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif char == ";" and depth == 0:
            sql = "".join(buffer).strip()
            if sql:
                statements.append({"sql": sql, "line": start_line})
            buffer = []
            index += 1
            start_line = line
            continue

        buffer.append(char)
        if char == "\n":
            line += 1
            if not "".join(buffer).strip():
                start_line = line
        index += 1

    tail = "".join(buffer).strip()
    if tail:
        statements.append({"sql": tail, "line": start_line})
    return statements


def dollar_tag_at(text, index):
    if not text.startswith("$", index):
        return ""
    cursor = index + 1
    while cursor < len(text) and (text[cursor].isalnum() or text[cursor] == "_"):
        cursor += 1
    if cursor < len(text) and text[cursor] == "$":
        return text[index : cursor + 1]
    return ""


def matching_paren(text, start):
    """`(` 위치에서 짝이 맞는 `)` 위치를 찾는다. 문자열 리터럴을 건너뛴다."""
    depth = 0
    index = start
    length = len(text)
    quote = None
    while index < length:
        char = text[index]
        if quote:
            if char == "\\" and index + 1 < length:
                index += 2
                continue
            if char == quote:
                if index + 1 < length and text[index + 1] == quote:
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


def tokenize(sql):
    """SQL 조각을 토큰 목록으로 나눈다. 괄호 묶음은 group 토큰 하나가 된다."""
    tokens = []
    index = 0
    length = len(sql)
    while index < length:
        char = sql[index]
        if char.isspace():
            index += 1
            continue
        if char in ("'", '"', "`"):
            cursor = index + 1
            while cursor < length:
                if sql[cursor] == "\\" and char == "'" and cursor + 1 < length:
                    cursor += 2
                    continue
                if sql[cursor] == char:
                    if cursor + 1 < length and sql[cursor + 1] == char:
                        cursor += 2
                        continue
                    cursor += 1
                    break
                cursor += 1
            tokens.append(Token("string" if char == "'" else "quoted", sql[index:cursor]))
            index = cursor
            continue
        if char == "(":
            end = matching_paren(sql, index)
            if end == -1:
                end = length - 1
            tokens.append(Token("group", sql[index : end + 1]))
            index = end + 1
            continue
        if char == "[":
            end = sql.find("]", index)
            if end == -1:
                end = length - 1
            tokens.append(Token("group", sql[index : end + 1]))
            index = end + 1
            continue
        if char.isalpha() or char == "_" or ord(char) > 127:
            cursor = index
            while cursor < length and (
                sql[cursor].isalnum() or sql[cursor] in "_$" or ord(sql[cursor]) > 127
            ):
                cursor += 1
            tokens.append(Token("word", sql[index:cursor]))
            index = cursor
            continue
        if char.isdigit():
            cursor = index
            while cursor < length and (sql[cursor].isdigit() or sql[cursor] == "."):
                if sql[cursor] == "." and cursor + 1 < length and not sql[cursor + 1].isdigit():
                    break
                cursor += 1
            tokens.append(Token("number", sql[index:cursor]))
            index = cursor
            continue
        for pair in PUNCT_PAIRS:
            if sql.startswith(pair, index):
                tokens.append(Token("punct", pair))
                index += len(pair)
                break
        else:
            tokens.append(Token("punct", char))
            index += 1
    return tokens


def split_top_level(text, separator=","):
    """괄호·문자열 밖의 구분자에서만 나눈다. 구분자는 결과에서 제외한다."""
    parts = []
    buffer = []
    depth = 0
    index = 0
    length = len(text)
    quote = None
    while index < length:
        char = text[index]
        if quote:
            buffer.append(char)
            if char == "\\" and index + 1 < length:
                buffer.append(text[index + 1])
                index += 2
                continue
            if char == quote:
                if index + 1 < length and text[index + 1] == quote:
                    buffer.append(quote)
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == separator and depth == 0:
            part = "".join(buffer).strip()
            if part:
                parts.append(part)
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    part = "".join(buffer).strip()
    if part:
        parts.append(part)
    return parts


def unquote(identifier):
    text = (identifier or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "`"):
        inner = text[1:-1]
        return inner.replace(text[0] * 2, text[0])
    if len(text) >= 2 and text[0] == "[" and text[-1] == "]":
        return text[1:-1]
    return text


def normalize_whitespace(text):
    return " ".join((text or "").split())
