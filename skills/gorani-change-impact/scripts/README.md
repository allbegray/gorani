# gorani-change-impact scripts

변경 영향 확인은 `입력 → 판정 → 리포트 모델 → 렌더러` 순서로 나뉩니다.

```text
change_impact.py            기존 CLI 진입점 (얇은 래퍼)
change_impact/
  __init__.py
  cli.py                    argparse, 경로 결정, 모델 생성, 렌더러 호출
  git.py                    git 명령, commit 해석, 변경 파일 조회
  manifest.py               sidecar manifest 탐색·파싱·글롭 매칭
  evaluate.py               manifest별 stale·clean·unknown 판정
  classify.py               full 모드 변경 분류
  model.py                  Markdown·JSON이 공유하는 리포트 모델
  render_md.py              Markdown 렌더러
  render_json.py            JSON 렌더러
  constants.py              분류 규칙·확인 제안·탐색 제외 디렉터리
```

## 데이터 흐름

1. `git.py`가 저장소 루트, HEAD, base, 변경 파일 목록을 읽습니다.
2. `manifest.py`가 `*.artifact.json`을 찾아 `sources`·`outputs`·`generated_commit`을 해석합니다.
3. `evaluate.py`가 manifest별로 stale·clean·unknown을 판정합니다.
4. `classify.py`가 full 모드에서 변경 파일을 frontend·api·db·config·dependencies·tests·docs로 나눕니다.
5. `model.py`가 JSON 직렬화 가능한 리포트 모델을 만들고, `render_md.py`·`render_json.py`가 같은 모델을 출력합니다.
6. `cli.py`가 옵션·출력 경로·exit code를 결정합니다.

## 커스터마이징 지점

- 분류 규칙·확인 제안 변경: `constants.py`
- stale·clean·unknown 판정 규칙 변경: `evaluate.py`
- 글롭 매칭·manifest 필드 해석 변경: `manifest.py`
- Markdown 구성·문장 변경: `render_md.py`
- JSON 필드 추가: `model.py`와 `render_json.py`
- 새 출력 형식 추가: `render_<format>.py` 추가 후 `cli.py`에서 호출

## 리포트 모델

- `impact-<head>-<mode>.json`이 리포트 모델입니다. 별도 `--model-out` 옵션은 없습니다.
- `schema_version`과 기존 `version` 필드를 함께 둡니다. 기존 소비자는 `version`과 기존 필드를 그대로 읽을 수 있습니다.
- 최상위 `mode`·`generated_at`·`base`·`head`·`manifest_glob`·`working`이 모델의 meta 역할을 합니다.
- `summary`는 집계, `stale`·`clean`·`unknown`은 manifest별 판정, `categories`·`suggestions`는 full 모드 결과, `warnings`는 전체 경고입니다.
- `schema_version`은 기존 소비자가 무시할 수 있는 추가 필드입니다. 기존 필드의 이름과 상대 순서는 유지합니다.

`model.py`·`evaluate.py`·`classify.py`·`render_*`는 표준 라이브러리만 사용합니다. 별도 패키지 설치가 필요하지 않습니다.
