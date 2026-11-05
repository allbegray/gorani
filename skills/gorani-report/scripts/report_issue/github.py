"""gh·git 명령 실행과 GitHub 이슈 생성·코멘트."""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as error:
        return None, str(error)
    return result, ""


def gh_available():
    return shutil.which("gh") is not None


def gh_authenticated():
    if not gh_available():
        return False, "gh 없음"
    result, error = run_command(["gh", "auth", "status"])
    if result is None:
        return False, error
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip() or "gh 인증 필요"
    return True, ""


def search_duplicates(repo, skill):
    result, error = run_command(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--search",
            skill,
            "--limit",
            "10",
            "--json",
            "number,title,url,state",
        ]
    )
    if result is None:
        return [], error
    if result.returncode != 0:
        return [], (result.stderr or result.stdout).strip() or "중복 검색 실패"
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return [], f"중복 검색 JSON 파싱 실패: {error}"
    if not isinstance(data, list):
        return [], "중복 검색 결과 형식이 올바르지 않습니다."
    return data, ""


def write_temp_body(body):
    handle, path = tempfile.mkstemp(prefix="gorani-report-", suffix=".md")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(body)
    return path


def create_issue(repo, title, body, label):
    path = write_temp_body(body)
    try:
        command = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body-file", path]
        if label:
            command += ["--label", label]
        result, error = run_command(command)
    finally:
        Path(path).unlink(missing_ok=True)
    if result is None:
        return False, error
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip() or "이슈 생성 실패"
    return True, result.stdout.strip()


def comment_issue(repo, number, body):
    path = write_temp_body(body)
    try:
        result, error = run_command(
            ["gh", "issue", "comment", str(number), "--repo", repo, "--body-file", path]
        )
    finally:
        Path(path).unlink(missing_ok=True)
    if result is None:
        return False, error
    if result.returncode != 0:
        return False, (result.stderr or result.stdout).strip() or "코멘트 생성 실패"
    return True, result.stdout.strip()
