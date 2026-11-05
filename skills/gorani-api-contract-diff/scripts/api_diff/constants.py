"""OpenAPI 계약 비교에서 공유하는 상수."""

METHODS = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]
SEVERITIES = ["breaking", "risky", "non-breaking", "info"]
PREFIXES = {"breaking": "B", "risky": "R", "non-breaking": "N", "info": "I"}
PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]
PRIORITY_LABELS = {
    "P0": "전면 중단",
    "P1": "배포 전 수정",
    "P2": "배포 전 확인",
    "P3": "호환성 확인",
    "P4": "참고",
}
