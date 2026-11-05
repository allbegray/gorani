"""입력 텍스트의 마스킹·길이 제한·잔여 위험 검사."""

import re
from pathlib import Path

from .constants import MAX_LOG, RISK_PATTERNS


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


def merge_redactions(target, counts):
    for label, count in counts.items():
        target[label] = target.get(label, 0) + count
    return target


def sanitize_values(raw):
    clipped = {}
    redactions = {}
    for key, value in raw.items():
        clean, counts = sanitize(value)
        clipped[key] = clip(clean)
        merge_redactions(redactions, counts)
    return clipped, redactions


def sanitize_tools(tools):
    cleaned = []
    redactions = {}
    for item in tools:
        clean, counts = sanitize(item)
        cleaned.append(clean)
        merge_redactions(redactions, counts)
    return cleaned, redactions
