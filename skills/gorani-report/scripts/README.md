# gorani-report scripts

이슈 드래프트 생성은 `입력 → 리포트 모델 → Markdown/JSON 렌더러` 순서로 나뉩니다.

```text
report_issue.py             기존 CLI 진입점 (얇은 래퍼)
report_issue/
  cli.py                    argparse, 실행 순서, 종료 코드, 렌더러 호출
  inputs.py                 CLI 인자·입력 파일 읽기
  environment.py            대상 SKILL.md 메타데이터와 실행 환경 수집
  sanitize.py               마스킹, 길이 제한, 잔여 위험 검사
  github.py                 gh·git 명령, 중복 검색, 이슈 생성·코멘트
  model.py                  JSON 직렬화 가능한 리포트 모델 생성
  render_md.py              이슈 본문 Markdown 렌더러
  render_json.py            결과·모델 JSON 렌더러
  draft.py                  드래프트 경로 결정과 저장
  constants.py              저장소·종류·영역·위험 패턴 상수
```

## 데이터 흐름

1. `inputs.py`가 인자와 입력 파일을 읽고, `sanitize.py`가 홈·작업 경로, 토큰, 자격증명, 이메일, 내부 URL을 마스킹합니다.
2. `environment.py`가 대상 스킬의 `SKILL.md` 메타데이터, git commit, OS, Python, Shell, `--tool` 값을 모읍니다.
3. `model.py`가 제목과 리포트 모델을 만듭니다. 모델은 `schema_version`·`meta`·`summary`·`values`·`environment`·`body`·`duplicates`·마스킹·위험·인증·생성 결과를 담습니다.
4. `render_md.py`가 모델의 값과 환경으로 이슈 본문을 만들고, `render_json.py`가 `--json` 결과와 `--model-out` 모델을 직렬화합니다.
5. `github.py`가 중복 검색과 이슈 생성·코멘트를 수행합니다.
6. `cli.py`가 전체 순서, 드래프트 경로, 종료 코드를 결정합니다.

## 커스터마이징 지점

- 본문 구성·문장 변경: `render_md.py`
- JSON 모델 필드 추가: `model.py`와 `render_json.py`
- 마스킹·위험 패턴 변경: `sanitize.py`와 `constants.py`
- 중복 검색·이슈 생성 명령 변경: `github.py`
- 스킬 버전·환경 수집 변경: `environment.py`
- 렌더링 전 데이터를 JSON으로 얻기: `python3 report_issue.py ... --model-out report-model.json`

`--json`은 기존 필드 이름과 순서를 유지하는 호환 결과입니다. `--model-out`은 `schema_version`이 있는 리포트 모델을 추가로 저장하며, 출력 파일 이름과 드래프트 본문은 바꾸지 않습니다.

`model.py`·`sanitize.py`·`inputs.py`는 `gh`나 렌더링에 직접 의존하지 않습니다. GitHub 호출은 `github.py`, 파일 쓰기는 `draft.py`·`render_json.py`에 모여 있습니다.
