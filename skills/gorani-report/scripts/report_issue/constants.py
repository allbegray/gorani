"""gorani-report 리포트에서 공유하는 상수."""

DEFAULT_REPO = "allbegray/gorani"
SCHEMA_VERSION = 1

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
