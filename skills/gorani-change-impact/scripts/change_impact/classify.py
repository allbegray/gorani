"""변경 파일을 frontend·api·db·config·dependencies·tests·docs로 분류한다."""

from .constants import CATEGORY_RULES, PRIORITY
from .manifest import match_sources


def classify(files):
    categories = {}
    for category in PRIORITY + ["docs"]:
        patterns = CATEGORY_RULES.get(category, [])
        if category == "docs":
            patterns = ["docs/**", "**/*.md", "**/*.adoc"]
        matches = sorted(item for item in files if match_sources(item, patterns))
        if matches:
            categories[category] = matches
    return categories
