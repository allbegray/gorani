"""변경 영향 리포트 모델을 JSON으로 렌더링한다."""

import json
from pathlib import Path


def render_json(result, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
