#!/usr/bin/env python3
"""SBOM과 로컬 패키지 디렉터리에서 라이선스·저작권 정보를 수집해 입력 JSON을 만든다.

입력: CycloneDX JSON (syft 산출물), 저장소 루트
출력: license-input.json (notice_build.py 입력)
"""

import argparse
import json
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

LICENSE_FILE_RE = re.compile(r"^(licen[cs]e|copying|copyright)", re.I)
NOTICE_FILE_RE = re.compile(r"^notice", re.I)
COPYRIGHT_RE = re.compile(
    r"^\s*(?:portions\s+)?(?i:copyright)\s*(?:\([cC]\)|©)\s*\S+"
    r"|^\s*(?:portions\s+)?(?i:copyright)\s+\d{4}"
    r"|^\s*(?:portions\s+)?Copyright\s+[A-Z]"
)
COPYRIGHT_PLACEHOLDER_RE = re.compile(
    r"\[yyyy\]|\[name of copyright owner\]|<year>|<copyright", re.I
)
MAX_TEXT = 200_000


def parse_args():
    parser = argparse.ArgumentParser(description="라이선스 고지 입력 JSON 생성")
    parser.add_argument("--sbom", required=True, help="CycloneDX JSON 경로")
    parser.add_argument("--root", default=".", help="저장소 루트 (기본: 현재 디렉터리)")
    parser.add_argument("--out", default=".legal/licenses-input.json", help="출력 JSON 경로")
    parser.add_argument("--project", help="프로젝트명 (기본: package.json name)")
    parser.add_argument("--version", help="앱 버전 (기본: package.json version)")
    parser.add_argument("--runtime", help="npm ls --omit=dev --all --json 결과 파일")
    parser.add_argument("--include-dev", action="store_true", help="개발 의존성도 포함")
    parser.add_argument("--generated-at", help="생성 시각 강제 지정 (ISO 8601, 샘플 재생성용)")
    parser.add_argument("--sbom-command", help="로그에 기록할 SBOM 생성 명령")
    return parser.parse_args()


def read_text(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    return text[:MAX_TEXT]


def component_name_version(component):
    name = str(component.get("name", "")).strip()
    version = str(component.get("version", "")).strip()
    purl = str(component.get("purl", "")).strip()
    if purl.startswith("pkg:"):
        body = purl[4:].split("?")[0].split("#")[0]
        _, _, rest = body.partition("/")
        if "@" in rest:
            rest_name, _, rest_version = rest.rpartition("@")
            decoded = unquote(rest_name)
            if decoded:
                name = decoded
            if rest_version and not version:
                version = rest_version
        elif rest and not name:
            name = unquote(rest)
    return name, version, purl


def component_license(component):
    licenses = component.get("licenses") or []
    values = []
    for entry in licenses:
        if not isinstance(entry, dict):
            continue
        if entry.get("expression"):
            values.append(str(entry["expression"]).strip())
            continue
        license_info = entry.get("license") or {}
        value = license_info.get("id") or license_info.get("name")
        if value:
            values.append(str(value).strip())
    unique = []
    for value in values:
        if value and value not in unique:
            unique.append(value)
    return " OR ".join(unique)


def find_files(directory):
    license_path = None
    notice_path = None
    if not directory or not directory.is_dir():
        return license_path, notice_path
    entries = sorted(directory.iterdir())
    for entry in entries:
        if not entry.is_file():
            continue
        if LICENSE_FILE_RE.match(entry.name) and license_path is None:
            license_path = entry
        elif NOTICE_FILE_RE.match(entry.name) and notice_path is None:
            notice_path = entry
    if license_path is None:
        for entry in entries:
            if entry.is_dir() and entry.name.lower() in ("licenses", "license"):
                for child in sorted(entry.iterdir()):
                    if child.is_file() and LICENSE_FILE_RE.match(child.name):
                        license_path = child
                        break
                if license_path:
                    break
    return license_path, notice_path


def candidate_dirs(root, name, version):
    dirs = []
    if not name:
        return dirs
    normalized = name.replace("/", "+") if name.startswith("@") else name
    dirs.append(root / "node_modules" / name)
    if version:
        dirs.append(root / "node_modules" / ".pnpm" / f"{normalized}@{version}" / "node_modules" / name)
        dirs.append(Path.home() / ".pub-cache" / "hosted" / "pub.dev" / f"{name}-{version}")
        py_name = name.replace("-", "_")
        for base in (root / ".venv" / "lib", root / "venv" / "lib", root / ".venv" / "lib64", root / "venv" / "lib64"):
            if base.is_dir():
                for lib in base.iterdir():
                    dirs.append(lib / "site-packages" / f"{py_name}-{version}.dist-info")
    return [d for d in dirs if d.is_dir()]


def extract_copyrights(text):
    found = []
    for raw in text.splitlines():
        line = raw.strip().lstrip("#*/ ").strip()
        if not line or len(line) > 200:
            continue
        if not COPYRIGHT_RE.match(line):
            continue
        if COPYRIGHT_PLACEHOLDER_RE.search(line):
            continue
        if line not in found:
            found.append(line)
        if len(found) >= 3:
            break
    return found


def is_gnu_license(value):
    return "gpl" in (value or "").lower()


def load_package_json(root):
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def runtime_packages(path):
    if not path:
        return set()
    runtime_path = Path(path)
    if not runtime_path.is_file():
        sys.exit(f"런타임 의존성 파일이 없습니다: {runtime_path}")
    try:
        data = json.loads(runtime_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        sys.exit(f"런타임 의존성 JSON 을 읽지 못했습니다: {error}")

    found = set()

    def walk(node):
        dependencies = (node or {}).get("dependencies") or {}
        for name, value in dependencies.items():
            version = str((value or {}).get("version", "")).strip()
            found.add((name, version))
            found.add((name, ""))
            walk(value)

    walk(data)
    return found


def local_repository(directory):
    path = directory / "package.json"
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    value = data.get("repository")
    if isinstance(value, dict):
        value = value.get("url", "")
    return str(value or "").strip()


def repository_url(component):
    references = component.get("externalReferences") or []
    ranked = sorted(
        (ref for ref in references if isinstance(ref, dict) and ref.get("url")),
        key=lambda ref: 0 if ref.get("type") in ("vcs", "source-distribution") else 1,
    )
    return str(ranked[0]["url"]).strip() if ranked else ""


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    sbom_path = Path(args.sbom)
    if not sbom_path.is_file():
        sys.exit(f"SBOM 파일이 없습니다: {sbom_path}")
    try:
        sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"SBOM JSON 을 읽지 못했습니다: {error}")

    package_json = load_package_json(root)
    direct = set()
    for field in ("dependencies", "devDependencies", "optionalDependencies"):
        direct.update((package_json.get(field) or {}).keys())
    dev_only = set((package_json.get("devDependencies") or {}).keys())
    runtime = runtime_packages(args.runtime)

    packages = []
    skipped_no_purl = 0
    project_name = str(package_json.get("name", "")).strip()
    project_version = str(package_json.get("version", "")).strip()
    for component in sbom.get("components") or []:
        if str(component.get("type", "")).lower() == "file":
            continue
        name, version, purl = component_name_version(component)
        if not name:
            continue
        if not purl:
            skipped_no_purl += 1
            continue
        if name == project_name and (not project_version or version == project_version):
            continue
        license_value = component_license(component)
        license_text = ""
        license_source = ""
        notice_text = ""
        repository = ""
        for directory in candidate_dirs(root, name, version):
            if not repository:
                repository = local_repository(directory)
            license_path, notice_path = find_files(directory)
            if license_path:
                license_text = read_text(license_path)
                license_source = str(license_path.relative_to(root)) if root in license_path.parents else str(license_path)
            if notice_path:
                notice_text = read_text(notice_path)
            if license_text:
                break
        copyrights = extract_copyrights(notice_text)
        if not copyrights and license_text and not is_gnu_license(license_value):
            copyrights = extract_copyrights(license_text)
        if not copyrights and component.get("copyright"):
            copyrights = [str(component["copyright"]).strip()]

        if version and (name, version) in runtime:
            scope = "runtime"
        elif not version and (name, "") in runtime:
            scope = "runtime"
        elif name in dev_only and name not in (package_json.get("dependencies") or {}):
            scope = "dev"
        elif args.runtime:
            scope = "dev"
        else:
            scope = "unknown"

        if scope == "dev" and not args.include_dev:
            continue

        packages.append(
            {
                "name": name,
                "version": version,
                "license": license_value,
                "copyright": "\n".join(copyrights),
                "purl": purl,
                "repository": repository or repository_url(component),
                "scope": scope,
                "dependency": "direct" if name in direct else "transitive",
                "license_text": license_text,
                "license_source": license_source,
                "notice_text": notice_text,
            }
        )

    packages.sort(key=lambda item: (item["name"].lower(), item["version"]))
    missing_text = sum(1 for item in packages if not item["license_text"])
    if not packages:
        sys.exit(
            "수집된 패키지가 없습니다. SBOM 경로, --include-dev, 패키지 설치 상태를 확인하세요."
        )
    generated_at = args.generated_at or datetime.now().astimezone().isoformat(timespec="seconds")
    syft_command = args.sbom_command or (
        f"syft dir:{args.root} -o cyclonedx-json={args.sbom}"
    )
    output = {
        "project": args.project or package_json.get("name", ""),
        "app_version": args.version or package_json.get("version", ""),
        "generated_at": generated_at,
        "ecosystem": "npm" if package_json else "",
        "packages": packages,
        "logs": [
            {
                "tool": "syft",
                "command": syft_command,
                "status": "ok",
                "note": f"components {len(sbom.get('components') or [])}, skipped without purl {skipped_no_purl}",
            },
            {
                "tool": "collect_licenses",
                "command": shlex.join(sys.argv),
                "status": "ok",
                "note": f"packages {len(packages)}, license text missing {missing_text}",
            },
        ],
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(out_path),
                "packages": len(packages),
                "missing_text": missing_text,
                "runtime": sum(1 for p in packages if p["scope"] == "runtime"),
                "dev": sum(1 for p in packages if p["scope"] == "dev"),
                "unknown_scope": sum(1 for p in packages if p["scope"] == "unknown"),
                "unknown_license": sum(1 for p in packages if not p["license"]),
                "skipped_no_purl": skipped_no_purl,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
