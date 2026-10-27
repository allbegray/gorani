# 샘플 보고서

스킬이 만드는 엑셀·JSON 결과의 예시입니다. 입력 JSON을 함께 두어 같은 결과를 다시 만들 수 있습니다.

## cve-scan

| 파일 | 내용 |
| --- | --- |
| `vex-input.json` | 정규화된 스캔 결과 입력 |
| `cve-report-sample.xlsx` | VEX 엑셀 보고서 (요약, VEX 판정, 원본 findings, 실행 로그) |
| `cve-report-sample.vex.json` | OpenVEX JSON |

VEX 엑셀과 OpenVEX는 사용자가 요청했을 때만 생성되는 선택 산출물의 예시입니다. 요청하지 않으면 스캔 요약과 조치 목록만 만듭니다.

재생성:

```bash
python3 skills/cve-scan/scripts/vex_xlsx.py --input samples/cve-scan/vex-input.json --outdir samples/cve-scan --name cve-report-sample
```

## release-check

| 파일 | 내용 |
| --- | --- |
| `release-check-input.json` | 브랜치 diff 점검 항목 입력 |
| `release-check-sample.xlsx` | 릴리스 점검 엑셀 보고서 (요약, 점검 항목, 변경 파일, 커밋, 실행 로그) |

재생성:

```bash
python3 skills/release-check/scripts/release_xlsx.py --input samples/release-check/release-check-input.json --outdir samples/release-check --name release-check-sample
```

## license-notice

| 파일 | 내용 |
| --- | --- |
| `license-input.json` | SBOM 수집 결과 입력 |
| `third-party-notices.html` | 앱·백엔드에 게시하는 자기완결 고지 페이지 |
| `third-party-notices.md` | 같은 내용의 평문 |
| `third-party-notices-review.md` | 검토 필요 목록 (내부용, 배포 제외) |

재생성:

```bash
python3 skills/license-notice/scripts/notice_build.py --input samples/license-notice/license-input.json --outdir samples/license-notice --name third-party-notices --formats html,md,review
```

샘플 프로젝트와 `legacy-widget` 패키지는 가상입니다. 라이선스 원문은 실제 npm 패키지에서 가져왔고, unknown·전문 없음·copyleft 검토 항목을 함께 보여 줍니다.

샘플은 `html,md,review` 기본 형식으로 생성합니다. 엑셀은 `--formats xlsx`를 추가했을 때만 만듭니다.

## release-note

| 파일 | 내용 |
| --- | --- |
| `release-input.json` | 큐레이션된 릴리스 노트 입력 |
| `release-notes.html` | 고객용 자기완결 릴리스 노트 페이지 |
| `release-notes.md` | 고객용 긴 버전 (GitHub Release·문서) |
| `release-notes-short.txt` | 스토어 짧은 버전 (기본 500자) |
| `release-notes-store.txt` | 스토어 긴 버전 (기본 4,000자) |
| `release-notes-internal.md` | commit 매핑·검토 기록 (내부용, 배포 제외) |

재생성:

```bash
python3 skills/release-note/scripts/notes_build.py --input samples/release-note/release-input.json --outdir samples/release-note --name release-notes --formats html,md,short,store,internal
```

샘플 제품·버전·링크는 가상입니다. 깨지는 변경, 알려진 문제, 고객 문의 경로, 내부 commit 매핑을 함께 보여 줍니다.

샘플은 전체 형식으로 생성합니다. 실제 프로젝트에서는 필요한 형식만 `--formats`로 지정합니다.

## 주의

- 샘플 데이터는 형식을 보여주기 위한 가상 데이터입니다. 실제 프로젝트 결과가 아닙니다.
- cve-scan·release-check 샘플과 license-notice의 `--xlsx`는 `openpyxl`이 필요합니다: `python3 -m pip install --user openpyxl`
- release-note는 표준 라이브러리만 사용합니다.
- 스크립트나 시트 구성을 바꾸면 샘플도 다시 생성해 같은 변경에 포함합니다.
