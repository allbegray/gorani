"""finding 우선순위(P0~P4) 계산."""

import re

from .constants import PRIORITIES

def is_response(location: str) -> bool:
    return bool(
        re.match(
            r"^(?:PATH|GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|TRACE) \S+ (?:\d{3}|default|[1-5]xx)\b",
            location,
        )
    )


def priority_of(finding: dict) -> str:
    severity = finding["severity"]
    message = finding["message"]
    location = finding["location"]
    if severity == "info":
        return "P4"
    if severity == "non-breaking":
        return "P4"
    if severity == "risky":
        return "P3"
    if "모든 API 경로가 제거" in message:
        return "P0"
    if location == "security" or location.startswith("securitySchemes."):
        return "P1"
    if "서버 URL" in message or "경로가 제거" in message or "오퍼레이션이 제거" in message:
        return "P1"
    if "요청 본문" in message or "요청 미디어 타입" in message or "파라미터가 추가" in message:
        return "P1"
    if "필수 필드가 추가" in message:
        return "P2" if is_response(location) else "P1"
    if "필수 여부가 변경" in message:
        return "P1" if finding["new"] == "True" else "P4"
    if "필드가 제거" in message or "허용 값이 제거" in message or "타입이 변경" in message:
        return "P2" if is_response(location) else "P1"
    if "파라미터가 제거" in message:
        return "P2" if is_response(location) else "P1"
    if "응답 상태 코드가 제거" in message or "응답 미디어 타입이 제거" in message:
        return "P2"
    return "P2"


def priority_rank(priority: str) -> int:
    return PRIORITIES.index(priority) if priority in PRIORITIES else len(PRIORITIES)


def group_priority(findings: list[dict]) -> str:
    if not findings:
        return "P4"
    return min((priority_of(finding) for finding in findings), key=priority_rank)
