"""사이트 구조도 생성에서 공유하는 상수."""

SCHEMA_VERSION = 1
OUTPUT_FORMATS = ("md", "xlsx", "html")
DEFAULT_FORMATS = "xlsx,md,html"
STATUSES = {"active", "planned", "deprecated"}
REVIEW_QUESTIONS = [
    "메뉴 depth가 실제 프론트 메뉴 구조와 일치하는가?",
    "상세·탭·액션 화면이 부모 화면으로 연결됐는가?",
    "API only가 화면 구조도와 분리됐는가?",
    "스크린샷 경로가 실제 화면과 일치하는가?",
    "KRDS 메인 메뉴 최대 3Depth 기준을 지켰는가?",
]
