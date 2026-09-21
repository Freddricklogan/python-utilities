"""A JSON file store with atomic writes. Each utility keeps its records in one file under a base
directory (default ~/.pyutils), so nothing is written where the user did not ask."""

from __future__ import annotations

import json
import os
from pathlib import Path


def default_dir() -> Path:
    return Path(os.environ.get("PYUTILS_HOME", str(Path.home() / ".pyutils")))


def read_json(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"{path} must contain a JSON list"
        raise ValueError(msg)
    return data


def write_json(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
