"""패키지 정규화, 라이선스 그룹화, 리포트 모델 생성을 담당한다."""

import difflib
import hashlib
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from .classify import canonical_license, classify
from .constants import (
    COPYRIGHT_LINE_RE,
    GENERATOR,
    GITHUB_REPO_RE,
    SCHEMA_VERSION,
    TEXT_SIMILARITY,
    UNKNOWN_LICENSE,
)


def normalize_packages(raw_packages):
    merged = {}
    for item in raw_packages:
        name = str(item.get("name", "")).replace("\n", " ").strip()
        if not name:
            continue
        version = str(item.get("version", "")).replace("\n", " ").strip()
        key = (name, version)
        license_value = str(item.get("license", "")).replace("\n", " ").strip()
        entry = merged.get(key)
        if entry is None:
            entry = {
                "name": name,
                "version": version,
                "license": license_value,
                "copyright": str(item.get("copyright", "")).strip(),
                "repository": str(item.get("repository", "")).strip(),
                "license_url": str(item.get("license_url", "")).strip(),
                "scope": str(item.get("scope", "unknown")).strip().lower() or "unknown",
                "dependency": str(item.get("dependency", "")).strip(),
                "license_text": str(item.get("license_text", "")),
                "license_source": str(item.get("license_source", "")).strip(),
                "notice_text": str(item.get("notice_text", "")).strip(),
            }
            merged[key] = entry
        else:
            if not entry["license"] and license_value:
                entry["license"] = license_value
            elif license_value and license_value not in entry["license"]:
                entry["license"] = (
                    f"{entry['license']} OR {license_value}" if entry["license"] else license_value
                )
            for field in ("copyright", "repository", "license_url", "license_source"):
                if not entry[field] and item.get(field):
                    entry[field] = str(item[field]).strip()
            if not entry["license_text"] and item.get("license_text"):
                entry["license_text"] = str(item["license_text"])
            if not entry["notice_text"] and item.get("notice_text"):
                entry["notice_text"] = str(item["notice_text"]).strip()
            if entry["scope"] == "unknown" and item.get("scope") in ("runtime", "dev"):
                entry["scope"] = str(item["scope"])
            if item.get("dependency") == "direct":
                entry["dependency"] = "direct"

    packages = []
    for entry in merged.values():
        entry["license"] = canonical_license(entry["license"])
        entry["status"] = classify(entry["license"])
        packages.append(entry)
    packages.sort(key=lambda item: (item["name"].lower(), item["version"], item["license"].lower()))
    return packages


def group_notices(packages):
    """라이선스별로 묶고, 표기 차이만 있는 같은 전문은 한 번만 수록한다."""
    groups = {}
    for package in packages:
        name = package["license"] or UNKNOWN_LICENSE
        group = groups.setdefault(name, {"license": name, "variants": {}, "missing": []})
        if not package["license_text"]:
            group["missing"].append(package)
            continue
        normalized = normalized_words(package["license_text"])
        match = None
        best = 0.0
        for key, variant in group["variants"].items():
            matcher = difflib.SequenceMatcher(None, normalized, variant["normalized"])
            if matcher.quick_ratio() < TEXT_SIMILARITY:
                continue
            ratio = matcher.ratio()
            if ratio > best:
                best = ratio
                match = key
        if match is not None and best >= TEXT_SIMILARITY:
            group["variants"][match]["packages"].append(package)
            continue
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        group["variants"][digest] = {
            "digest": digest,
            "text": package["license_text"],
            "normalized": normalized,
            "packages": [package],
        }

    ordered = []
    for name in sorted(groups, key=lambda value: (value == UNKNOWN_LICENSE, value.lower())):
        group = groups[name]
        variants = sorted(
            group["variants"].values(),
            key=lambda variant: variant["packages"][0]["name"].lower(),
        )
        ordered.append(
            {
                "license": group["license"],
                "variants": variants,
                "missing": sorted(group["missing"], key=lambda p: p["name"].lower()),
            }
        )
    return ordered


def normalized_words(text):
    """저작권 줄과 줄바꿈·따옴표 차이를 지워 전문의 뼈대를 비교한다."""
    lines = [line for line in text.splitlines() if not COPYRIGHT_LINE_RE.search(line)]
    lowered = "\n".join(lines).lower().replace("licence", "license")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", lowered)).strip()


def package_label(package):
    return f"{package['name']} {package['version']}".strip()


def copyright_line(package):
    return " · ".join(
        line.strip() for line in package.get("copyright", "").splitlines() if line.strip()
    )


def github_repository_url(repository: str) -> str:
    text = str(repository or "").strip()
    if not text:
        return ""
    text = text.split("#", 1)[0].strip()
    if text.startswith("git+"):
        text = text[4:]
    if text.startswith("git@github.com:"):
        text = "https://github.com/" + text[len("git@github.com:") :]
    elif text.startswith("ssh://git@github.com/"):
        text = "https://github.com/" + text[len("ssh://git@github.com/") :]
    elif text.startswith("git://github.com/"):
        text = "https://github.com/" + text[len("git://github.com/") :]
    elif text.startswith("github:"):
        text = "https://github.com/" + text[len("github:") :]
    elif re.match(r"^[\w.-]+/[\w.-]+$", text):
        text = "https://github.com/" + text
    if text.startswith("github.com/"):
        text = "https://" + text
    text = text.rstrip("/")
    match = GITHUB_REPO_RE.match(text)
    if not match:
        return ""
    owner, repo = match.group(1), match.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return f"https://github.com/{owner}/{repo}"


def license_file_name(package: dict) -> str:
    source = str(package.get("license_source", "")).strip()
    if source:
        name = Path(source).name
        if name:
            return name
    return "LICENSE"


def github_license_url(package: dict) -> str:
    explicit = str(package.get("license_url", "")).strip()
    if explicit:
        return explicit
    base = github_repository_url(package.get("repository", ""))
    if not base:
        return ""
    return f"{base}/blob/HEAD/{quote(license_file_name(package), safe='')}"


def model_groups(groups):
    """렌더러가 소비할 그룹 목록. 내부 비교용 normalized 필드는 뺀다."""
    return [
        {
            "license": group["license"],
            "variants": [
                {
                    "digest": variant["digest"],
                    "text": variant["text"],
                    "packages": variant["packages"],
                }
                for variant in group["variants"]
            ],
            "missing": group["missing"],
        }
        for group in groups
    ]


def model_warnings(packages, mode):
    warnings = []

    def add(code, message, items):
        if items:
            warnings.append(
                {
                    "code": code,
                    "message": message,
                    "packages": [package_label(package) for package in items],
                }
            )

    add(
        "missing-license-text",
        "라이선스 전문이 없습니다.",
        [package for package in packages if not package["license_text"]],
    )
    add(
        "unknown-license",
        "라이선스를 확인하지 못했습니다.",
        [package for package in packages if package["status"] == "unknown"],
    )
    if mode == "simple":
        add(
            "missing-github-link",
            "GitHub 라이선스 링크를 만들 수 없습니다.",
            [package for package in packages if not github_license_url(package)],
        )
    return warnings


def build_report_model(data, packages, groups, review, name="", mode="full"):
    status_counts = Counter(package["status"] for package in packages)
    scope_counts = Counter(package["scope"] for package in packages)
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "generator": GENERATOR,
            "project": str(data.get("project", "")),
            "app_version": str(data.get("app_version", "")),
            "generated_at": str(data.get("generated_at", "")),
            "ecosystem": str(data.get("ecosystem", "")),
            "mode": mode,
            "name": name,
        },
        "summary": {
            "packages": len(packages),
            "licenses": len(
                {package["license"] or UNKNOWN_LICENSE for package in packages}
            ),
            "license_texts": sum(len(group["variants"]) for group in groups),
            "review_items": len(review),
            "missing_license_text": sum(
                1 for package in packages if not package["license_text"]
            ),
            "missing_github_links": sum(
                1 for package in packages if not github_license_url(package)
            ),
            "status": dict(status_counts),
            "scope": dict(scope_counts),
        },
        "packages": packages,
        "groups": model_groups(groups),
        "review": review,
        "warnings": model_warnings(packages, mode),
        "logs": data.get("logs", []),
    }
