# gorani-release-note scripts

릴리스 노트 생성은 `입력 → 리포트 모델 → 렌더러` 순서로 나뉩니다.

```text
notes_build.py              기존 CLI 진입점 (얇은 래퍼)
collect_changes.py          git 범위에서 입력 초안을 만드는 수집기
notes_build/
  cli.py                    argparse, 입력 확인, 모델 생성, 렌더러 호출
  model.py                  입력 정규화, 요약 자동 생성, commit 매핑, 리포트 모델
  validate.py               필수 값·배열·링크·지원 경로·글자 수 검사
  render_md.py              Markdown 렌더러
  render_html.py            자기완결 HTML 렌더러
  render_text.py            short·store 텍스트 렌더러
  render_internal.py        내부 검토용 Markdown 렌더러
  render_json.py            --model-out 리포트 모델 JSON 저장
  constants.py              라벨·글자 수 제한·출력 형식·스키마 버전
```

## 데이터 흐름

1. `cli.py`가 입력 JSON을 읽고 `validate.py`로 필수 값과 경고·strict 항목을 확인합니다.
2. `model.py`가 언어 라벨, 글자 수 제한, short/store 자동 생성 결과를 더해 JSON 직렬화 가능한 모델을 만듭니다.
3. `render_md.py`·`render_html.py`·`render_text.py`·`render_internal.py`가 같은 모델을 각 형식으로 렌더링합니다.
4. `render_json.py`가 `--model-out` 경로에 모델을 저장합니다. 저장은 렌더링 전에 합니다.
5. `cli.py`가 파일 이름과 콘솔 요약을 결정합니다.

## 리포트 모델

- `schema_version`: 모델 스키마 버전
- `meta`: `generator`, `generated_at`, 입력 경로, 제품·버전·배포일·언어·대상, 선택한 형식, 비교 범위
- `summary`: 섹션·항목·highlight·commit 포함/제외 수, short/store 글자 수와 제한, 자동 생성 여부
- `content`: 제품·버전·배포일, headline·summary, `sections`와 `items`, `highlights`, `breaking_changes`, `known_issues`, `upgrade_notes`, `support`
- `summaries`: 렌더링에 쓴 short·store 본문
- `limits`, `warnings`, `strict_issues`, `auto_notes`, `errors`, `commits`, `logs`
- `internal.mappings`: commit hash·날짜·제목·분류·포함 여부·note/reason
- `internal.included`, `internal.excluded`: 포함·제외 commit 수

`meta.generated_at`은 `--generated-at`, 입력의 `generated_at`, 현재 시각 순서로 정합니다. 고객용 md·html·txt에는 생성 시각을 넣지 않습니다.

## 커스터마이징 지점

- 고객 문구·구성 변경: `render_md.py`, `render_html.py`, `render_text.py`
- 내부 검토 표·확인 목록 변경: `render_internal.py`
- 모델 필드 추가: `model.py`
- 검증 규칙 변경: `validate.py`
- 새 출력 형식: `render_<형식>.py` 추가 후 `cli.py`에서 호출
- 렌더링 전 데이터를 JSON으로 얻기: `python3 notes_build.py ... --model-out report-model.json`

`model.py`·`validate.py`와 모든 렌더러는 표준 라이브러리만 사용합니다.
