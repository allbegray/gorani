# gorani-site-structure scripts

사이트 구조도 생성은 `입력 → 리포트 모델 → 렌더러` 순서로 나뉩니다.

```text
site_structure.py           기존 CLI 진입점 (얇은 래퍼)
site_structure/
  __init__.py
  cli.py                    argparse, 출력 경로, 소스 결정, 모델 저장, 렌더러 호출
  input.py                  입력 JSON 읽기와 페이지·표준·검토 메모 정규화
  model.py                  화면·API·표준·검토 집계와 리포트 모델 생성
  render_md.py              Markdown 렌더러
  render_html.py            자기완결 HTML 렌더러
  render_xlsx.py            XLSX 렌더러 (openpyxl)
  manifest.py               sidecar .artifact.json 생성
  constants.py              출력 형식·상태·검토 질문 상수
```

## 데이터 흐름

1. `input.py`가 `site-structure-input.json`을 읽고 페이지·표준·검토 메모를 정규화합니다.
2. `model.py`가 화면 수·depth·상태·API·표준·검토 집계와 `sources`를 더해 JSON 직렬화 가능한 리포트 모델을 만듭니다.
3. `render_md.py`, `render_html.py`, `render_xlsx.py`가 같은 모델을 각각의 출력 형식으로 렌더링합니다.
4. `manifest.py`가 산출물·소스·재생성 명령을 `.artifact.json`에 기록합니다.
5. `cli.py`가 전체 순서와 파일 이름을 결정합니다.

## 커스터마이징 지점

- Markdown 문장·표 구성 변경: `render_md.py`
- HTML 검색·메뉴 트리·스타일 변경: `render_html.py`
- Excel 시트·컬럼·스타일 변경: `render_xlsx.py`
- 집계·모델 필드 추가: `model.py`
- 입력 필드·정규화 규칙 변경: `input.py`
- 새 출력 형식 추가: `render_<format>.py` 추가 후 `cli.py`에서 호출
- 렌더링 전 데이터를 JSON으로 얻기: `python3 site_structure.py ... --model-out report.json`

리포트 모델은 `schema_version`, `generated_at`, `meta`, `summary`, `pages`, `api_only`, `standards`, `warnings`, `sources`를 담습니다. `--generated-at <ISO 8601>`은 manifest와 모델의 `generated_at`을 고정합니다.

`input.py`·`model.py`·`render_md.py`·`render_html.py`는 openpyxl을 import하지 않습니다. 따라서 모델과 Markdown·HTML 렌더링은 Excel 의존성 없이 테스트할 수 있습니다.
