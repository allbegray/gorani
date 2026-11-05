"""변경 영향 리포트 모델을 Markdown으로 렌더링한다."""


def build_markdown(result):
    summary = result["summary"]
    lines = [
        "# 변경 영향 — " + ("stale 확인" if result["mode"] == "stale" else "전체 요약"),
        "",
        f"- 모드: {result['mode']}",
        f"- 기준: {result['base']}",
        f"- HEAD: {result['head'] or '-'}",
        f"- 기준 시각: {result['generated_at']}",
        f"- 변경 파일: {summary['changed_files']}",
        f"- 갱신 필요: {summary['stale']}",
        f"- 변경 없음: {summary['clean']}",
        f"- 확인 불가: {summary['unknown']}",
    ]
    if result["mode"] == "full" and result["categories"]:
        lines.append("- 변경 분류: " + ", ".join(f"{key} {len(value)}" for key, value in result["categories"].items()))
    lines += ["", "## 갱신 필요", ""]
    if result["stale"]:
        lines += [
            "| 산출물 | 스킬 | 매칭된 변경 | 재생성 |",
            "| --- | --- | --- | --- |",
        ]
        for item in result["stale"]:
            matched = item["matched"][:8]
            text = "<br>".join(matched)
            if len(item["matched"]) > len(matched):
                text += f"<br>외 {len(item['matched']) - len(matched)}건"
            regenerate = item["regenerate"] or "-"
            lines.append(
                f"| `{item['artifact'] or item['manifest']}` | `{item['skill'] or '-'}` | {text or '-'} | `{regenerate}` |"
            )
    else:
        lines.append("- 갱신 필요 없음")
    if result["unknown"]:
        lines += ["", "## 확인 불가", ""]
        for item in result["unknown"]:
            errors = "; ".join(item["errors"]) or "원인 미확인"
            lines.append(f"- `{item['artifact'] or item['manifest']}` — {errors}")
    if result["mode"] == "full":
        lines += ["", "## 변경 분류", ""]
        if result["categories"]:
            for category, files in result["categories"].items():
                lines.append(f"- {category}: {len(files)}건")
                for path in files[:10]:
                    lines.append(f"  - `{path}`")
                if len(files) > 10:
                    lines.append(f"  - 외 {len(files) - 10}건")
        else:
            lines.append("- 분류된 변경 없음")
        lines += ["", "## 확인 제안", ""]
        if result["suggestions"]:
            for item in result["suggestions"]:
                lines.append(f"- `{item['skill']}` — {item['reason']}")
        else:
            lines.append("- 없음")
        lines += ["", "## 릴리스 절차", ""]
        lines.append("- 이 리포트를 확인한 뒤 `gorani-release-check` → `gorani-release-note` 순서로 진행합니다.")
    if result["warnings"]:
        lines += ["", "## 경고", ""]
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
    lines += [
        "",
        "> 이 리포트는 산출물을 수정하지 않습니다. 표시된 갱신 명령을 확인한 뒤 사용자가 직접 실행합니다.",
        "",
    ]
    return "\n".join(lines)
