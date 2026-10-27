# 샘플 보고서

스킬이 만드는 엑셀·JSON 결과의 예시입니다. 입력 JSON을 함께 두어 같은 결과를 다시 만들 수 있습니다.

## cve-scan

| 파일 | 내용 |
| --- | --- |
| `vex-input.json` | 정규화된 스캔 결과 입력 |
| `cve-report-sample.xlsx` | VEX 엑셀 보고서 (요약, VEX 판정, 원본 findings, 실행 로그) |
| `cve-report-sample.vex.json` | OpenVEX JSON |

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

## 주의

- 샘플 데이터는 형식을 보여주기 위한 가상 데이터입니다. 실제 프로젝트 결과가 아닙니다.
- `openpyxl`이 필요합니다: `python3 -m pip install --user openpyxl`
- 스크립트나 시트 구성을 바꾸면 샘플도 다시 생성해 같은 변경에 포함합니다.
