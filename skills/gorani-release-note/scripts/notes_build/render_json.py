"""리포트 모델을 JSON 파일로 저장한다."""

import json
from pathlib import Path


def render_model(model, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path
