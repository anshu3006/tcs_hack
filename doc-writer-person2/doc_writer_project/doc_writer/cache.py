"""
Tiny file-based cache keyed by (endpoint content hash + prompt version).

Avoids re-calling the LLM for endpoints that haven't changed since the last
run - saves API calls/cost during iteration and makes reruns near-instant.
Not meant to be clever: one JSON file per cache entry under .cache/.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(os.getenv("DOC_WRITER_CACHE_DIR", ".cache"))


def endpoint_hash(endpoint: dict, prompt_version: str) -> str:
    payload = json.dumps(endpoint, sort_keys=True) + "|" + prompt_version
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def get(key: str) -> Optional[dict]:
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def set(key: str, value: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{key}.json").write_text(
        json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
    )
