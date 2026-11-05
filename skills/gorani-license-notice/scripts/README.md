# gorani-license-notice scripts

고지 페이지 생성은 `입력 수집 → 리포트 모델 → 렌더러` 순서로 나뉩니다.

```text
collect_licenses.py         SBOM·설치 패키지에서 라이선스 입력 JSON 수집
notice_build.py             기존 CLI 진입점 (얇은 래퍼)
notice_build/
  cli.py                    argparse, 출력 경로, 모델 저장, 렌더러 호출
  classify.py               SPDX 표현 정규화와 고지 의무 분류 (OR/AND)
  model.py                  패키지 병합·정렬, 라이선스 그룹화, 리포트 모델 생성
  review.py                 검토 항목 계산과 검토 Markdown 렌더링
  render_md.py              전체·간소화 Markdown 렌더러
  render_html.py            전체·간소화 자기완결 HTML 렌더러
  render_xlsx.py            XLSX 렌더러 (openpyxl)
  constants.py              상태·정책·페이지 상수
```

## 데이터 흐름

1. `collect_licenses.py`가 CycloneDX SBOM과 설치된 패키지의 LICENSE·NOTICE를 읽어 입력 JSON을 만듭니다.
2. `cli.py`가 입력 JSON을 읽고 `--exclude-dev`를 적용합니다.
3. `model.py`가 패키지를 이름·버전으로 병합하고 정렬한 뒤, 라이선스별 전문 그룹을 만듭니다.
4. `model.py`의 `build_report_model`이 `schema_version`·`meta`·`summary`·`packages`·`groups`·`review`·`warnings`·`logs`를 담은 JSON 직렬화 가능 모델을 만듭니다.
5. `render_md.py`·`render_html.py`·`render_xlsx.py`가 같은 모델을 각 형식으로 렌더링합니다.
6. `cli.py`가 파일 이름, stdout 요약, `--fail-on-review` 종료 코드를 결정합니다.

## 리포트 모델

`--model-out PATH`로 렌더링 전 모델을 저장합니다.

- `schema_version`: 모델 스키마 버전 (현재 1)
- `meta`: `generator`, `project`, `app_version`, `generated_at`, `ecosystem`, `mode`, `name`
- `summary`: `packages`, `licenses`, `license_texts`, `review_items`, `missing_license_text`, `missing_github_links`, `status`, `scope`
- `packages`: 정규화된 패키지 목록
- `groups`: 라이선스별 `variants`와 `missing` 목록. `--simple`은 빈 배열
- `review`: 검토 항목의 `package`, `reason`, `action`
- `warnings`: `missing-license-text`, `unknown-license`, `missing-github-link` 데이터 경고
- `logs`: 입력 JSON의 실행 로그

`--generated-at`으로 `meta.generated_at`과 출력의 생성 시각을 고정할 수 있습니다. 지정하지 않으면 입력의 `generated_at`, 그것도 없으면 현재 시각을 씁니다.

## 커스터마이징 지점

- 출력 문구·구성 변경: `render_md.py`, `render_html.py`
- 엑셀 시트·스타일 변경: `render_xlsx.py`
- 검토 사유·조치 변경: `review.py`
- 라이선스 분류·별칭 변경: `classify.py`와 `constants.py`
- 패키지 병합·정렬·그룹화 변경: `model.py`
- 새 출력 형식 추가: `render_<format>.py` 추가 후 `cli.py`에서 호출
- 렌더링 전 데이터를 JSON으로 얻기: `python3 notice_build.py ... --model-out report.json`

`render_xlsx.py`만 openpyxl을 import합니다. `model.py`·`classify.py`·`review.py`·`render_md.py`·`render_html.py`는 openpyxl 없이 import할 수 있고, `--model-out`과 HTML·Markdown 생성도 openpyxl 없이 동작합니다.
