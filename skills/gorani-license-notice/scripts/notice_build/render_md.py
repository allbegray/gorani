"""Markdown 고지 페이지와 간소화 Markdown 렌더러."""

import re

from .constants import PAGE_TITLE
from .model import copyright_line, github_license_url, package_label


def fence(text):
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    marker = "`" * max(3, longest + 1)
    return f"{marker}\n{text.rstrip()}\n{marker}"


def build_simple_markdown(model):
    meta = model["meta"]
    packages = model["packages"]
    project = str(meta.get("project", ""))
    version = str(meta.get("app_version", ""))
    generated_at = str(meta.get("generated_at", ""))[:10]
    title = " ".join(part for part in (project, version) if part)
    lines = [f"# {PAGE_TITLE}", ""]
    if title:
        lines.extend([f"**{title}**", ""])
    if generated_at:
        lines.extend([f"Generated: {generated_at}", ""])
    lines.extend(["| Dependency | Version | License |", "| --- | --- | --- |"])
    for package in packages:
        name = str(package["name"]).replace("|", "\\|").replace("\n", " ")
        package_version = str(package["version"]).replace("|", "\\|").replace("\n", " ")
        url = github_license_url(package)
        license_link = f"[LICENSE]({url})" if url else "-"
        lines.append(f"| {name} | {package_version} | {license_link} |")
    return "\n".join(lines) + "\n"


def build_markdown(model):
    meta = model["meta"]
    groups = model["groups"]
    project = str(meta.get("project", ""))
    version = str(meta.get("app_version", ""))
    generated_at = str(meta.get("generated_at", ""))
    lines = [f"# {PAGE_TITLE}", ""]
    title = " ".join(part for part in (project, version) if part)
    if title:
        lines.extend([f"**{title}**", ""])
    if generated_at:
        lines.extend([f"Generated: {str(generated_at)[:10]}", ""])
    lines.extend(
        [
            "This product includes the third-party software listed below. "
            "Each license text and copyright notice is reproduced for attribution. "
            "Where libraries share the same license, the text appears once and each "
            "copyright notice is listed with its library.",
            "",
        ]
    )
    for group in groups:
        lines.extend([f"## {group['license']}", ""])
        for variant in group["variants"]:
            lines.extend(["Applies to:", ""])
            for package in variant["packages"]:
                line = f"- {package_label(package)}"
                notice = copyright_line(package)
                if notice:
                    line += f" — {notice}"
                lines.append(line)
            lines.extend(["", "License text:", "", fence(variant["text"]), ""])
            seen_notices = []
            for package in variant["packages"]:
                notice_text = package.get("notice_text", "").strip()
                if notice_text and notice_text not in seen_notices:
                    seen_notices.append(notice_text)
            for notice_text in seen_notices:
                lines.extend(["NOTICE:", "", fence(notice_text), ""])
        if group["missing"]:
            lines.extend(["License text not found for:", ""])
            for package in group["missing"]:
                lines.append(f"- {package_label(package)}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
