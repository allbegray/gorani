"""스토어용 짧은·긴 텍스트를 렌더링한다."""


def render_short(model):
    return model.get("summaries", {}).get("short", "").rstrip() + "\n"


def render_store(model):
    return model.get("summaries", {}).get("store", "").rstrip() + "\n"
