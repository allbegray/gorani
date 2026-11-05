"""리포트 결과·모델을 JSON으로 렌더링한다."""

import json
from pathlib import Path


def render_result(result):
    return json.dumps(result, ensure_ascii=False, indent=2)


def write_model(model, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path
