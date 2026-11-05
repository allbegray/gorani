"""오픈소스 고지 페이지 리포트에서 공유하는 상수."""

import re

STATUS_LABELS = {
    "none": "고지 불필요",
    "notice": "고지 필요",
    "weak": "소스 공개 검토(약)",
    "strong": "소스 공개 검토(강)",
    "network": "네트워크 공개 검토",
    "unknown": "확인 필요",
}
RANK = {"none": 0, "notice": 1, "weak": 2, "strong": 3, "network": 4, "unknown": 5}

POLICY = {
    "0BSD": "none",
    "MIT-0": "none",
    "Unlicense": "none",
    "CC0-1.0": "none",
    "WTFPL": "none",
    "MIT": "notice",
    "ISC": "notice",
    "BSD-2-Clause": "notice",
    "BSD-3-Clause": "notice",
    "Apache-2.0": "notice",
    "Zlib": "notice",
    "BSL-1.0": "notice",
    "Python-2.0": "notice",
    "MPL-2.0": "weak",
    "EPL-2.0": "weak",
    "CDDL-1.0": "weak",
    "LGPL-2.1-only": "weak",
    "LGPL-2.1-or-later": "weak",
    "LGPL-3.0-only": "weak",
    "LGPL-3.0-or-later": "weak",
    "GPL-2.0-only": "strong",
    "GPL-2.0-or-later": "strong",
    "GPL-3.0-only": "strong",
    "GPL-3.0-or-later": "strong",
    "AGPL-3.0-only": "network",
    "AGPL-3.0-or-later": "network",
}

ALIASES = {
    "mit license": "MIT",
    "expat": "MIT",
    "apache 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "asl 2.0": "Apache-2.0",
    "bsd": "BSD-3-Clause",
    "new bsd": "BSD-3-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "bsd 2-clause": "BSD-2-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "isc license": "ISC",
    "mozilla public license 2.0": "MPL-2.0",
    "mpl 2.0": "MPL-2.0",
    "gpl-3.0": "GPL-3.0-only",
    "gplv3": "GPL-3.0-only",
    "gpl-2.0": "GPL-2.0-only",
    "gplv2": "GPL-2.0-only",
    "lgpl-3.0": "LGPL-3.0-only",
    "lgpl-2.1": "LGPL-2.1-only",
    "agpl-3.0": "AGPL-3.0-only",
}

EXCEL_TEXT_LIMIT = 30_000
OUTPUT_FORMATS = ("html", "md", "review", "xlsx")
SIMPLE_FORMATS = ("html", "md")
DEFAULT_FORMATS = "html,md,review"
GITHUB_REPO_RE = re.compile(r"^https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$", re.I)
UNKNOWN_LICENSE = "Unknown license"
PAGE_TITLE = "Third-Party Notices"
COPYRIGHT_LINE_RE = re.compile(r"^\s*copyright\b|\(c\)|©", re.I)
TEXT_SIMILARITY = 0.97

SCHEMA_VERSION = 1
GENERATOR = "gorani-license-notice"
