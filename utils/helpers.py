import json
from pathlib import Path
from datetime import datetime


def load_json(filepath: str) -> dict | list:
    path = Path(filepath)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath: str, data: dict | list) -> None:
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def sanitize_input(text: str) -> str:
    return text.strip().replace("\n", " ")
