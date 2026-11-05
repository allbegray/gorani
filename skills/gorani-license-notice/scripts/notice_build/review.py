"""검토 필요 항목 계산과 검토 Markdown 렌더링."""

import re

from .constants import RANK


def review_items(packages):
    items = []
    for package in packages:
        reasons = []
        actions = []
        if package["status"] in ("weak", "strong", "network"):
            reasons.append("copyleft 라이선스, 소스 공개 범위 검토 필요")
            actions.append("법무 검토 후 배포 여부와 소스 공개 범위 결정")
        if package["status"] == "unknown":
            reasons.append("라이선스 확인 필요")
            actions.append("저장소의 LICENSE 원문을 확인해 license 값 보정")
        if re.search(r"\s+(OR|AND)\s+", package["license"], re.I):
            reasons.append("복수 라이선스 표현, 적용 조건 확인 필요")
            actions.append("배포에 적용할 라이선스를 정하고 해당 전문이 수록됐는지 확인")
        if not package["license_text"]:
            reasons.append("라이선스 전문 없음")
            actions.append("저장소에서 LICENSE 원문을 받아 license_text 채우기")
        if package["scope"] == "dev":
            reasons.append("개발 의존성, 배포 대상 여부 확인 필요")
            actions.append("앱 산출물에 포함되지 않으면 packages 에서 제외")
        if reasons:
            items.append(
                {
                    "package": package,
                    "reason": " / ".join(reasons),
                    "action": " / ".join(actions),
                }
            )
    items.sort(
        key=lambda item: (
            -RANK[item["package"]["status"]],
            item["package"]["name"].lower(),
        )
    )
    return items


def build_review_markdown(model):
    review = model["review"]
    meta = model["meta"]
    lines = [
        "# 고지 검토 필요",
        "",
        f"- 프로젝트: {meta.get('project', '')}",
        f"- 앱 버전: {meta.get('app_version', '')}",
        f"- 생성 시각: {meta.get('generated_at', '')}",
        f"- 검토 항목: {len(review)}",
        "",
        "이 파일은 내부 검토용입니다. 앱이나 배포 페이지에 포함하지 않습니다.",
        "",
        "| 패키지 | 버전 | 라이선스 | 사유 | 조치 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in review:
        package = item["package"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(package["name"]).replace("|", "\\|"),
                    str(package["version"]).replace("|", "\\|"),
                    (package["license"] or "unknown").replace("|", "\\|"),
                    item["reason"].replace("|", "\\|"),
                    item["action"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"
