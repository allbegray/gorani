# gorani-api-contract-diff scripts

OpenAPI 계약 비교는 `스펙 로딩 → 비교 → 리포트 모델 → 렌더러` 순서로 나뉩니다.

```text
api_diff.py                 기존 CLI 진입점 (얇은 래퍼)
api_diff/
  cli.py                    argparse, 출력 경로, 모델 생성, 렌더러 호출
  compare.py                스펙 로딩, $ref 해석, 계약 비교
  priority.py               P0~P4 우선순위 계산
  model.py                  Markdown·JSON이 공유하는 리포트 모델
  render_md.py              Markdown 렌더러
  render_json.py            JSON 렌더러
  manifest.py               sidecar .artifact.json 생성
  constants.py              심각도·우선순위·HTTP 메서드 상수
```

## 데이터 흐름

1. `compare.py`가 이전·새 스펙을 읽고 findings·body_changes·unresolved_refs를 만듭니다.
2. `model.py`가 서비스·버전·클라이언트·생성 시각과 집계를 더해 리포트 모델을 만듭니다.
3. `render_md.py`와 `render_json.py`가 같은 모델을 각각의 형식으로 렌더링합니다.
4. `manifest.py`가 산출물·소스·재생성 명령을 기록합니다.

## 커스터마이징 지점

- Markdown 구성·문장 변경: `render_md.py`
- JSON 필드 추가: `model.py`와 `render_json.py`
- 새 출력 형식: `render_<format>.py` 추가 후 `cli.py`에서 호출
- 비교 규칙·심각도 변경: `compare.py`
- 우선순위 규칙 변경: `priority.py`

`compare.py`·`priority.py`·`model.py`는 PyYAML과 출력 렌더링에 직접 의존하지 않습니다. YAML 입력은 `compare.py`의 선택적 import로만 처리합니다.
