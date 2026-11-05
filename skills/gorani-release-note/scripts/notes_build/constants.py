"""릴리스 노트 생성에서 공유하는 상수."""

SCHEMA_VERSION = 1
GENERATOR = "gorani-release-note"

LABELS = {
    "ko": {
        "release_notes": "릴리스 노트",
        "date": "배포일",
        "audience": "대상",
        "highlights": "한눈에 보기",
        "breaking": "업그레이드 전 확인",
        "known_issues": "알려진 문제",
        "upgrade_notes": "업그레이드 참고",
        "support": "도움이 필요하신가요?",
        "how_to_use": "사용 방법",
        "action": "조치",
        "learn_more": "자세히 보기",
        "update": "업데이트",
        "see_app": "자세한 내용은 앱에서 확인해 주세요.",
        "details": "자세한 내용",
    },
    "en": {
        "release_notes": "Release notes",
        "date": "Released",
        "audience": "Audience",
        "highlights": "Highlights",
        "breaking": "Before you upgrade",
        "known_issues": "Known issues",
        "upgrade_notes": "Upgrade notes",
        "support": "Need help?",
        "how_to_use": "How to use",
        "action": "Action",
        "learn_more": "Learn more",
        "update": "update",
        "see_app": "See the app for details.",
        "details": "Details",
    },
}

DEFAULT_LIMITS = {"short": 500, "store": 4000}
OUTPUT_FORMATS = ("html", "md", "short", "store", "internal")
DEFAULT_FORMATS = ",".join(OUTPUT_FORMATS)
