"""
Chains: Extractor (Person 1) -> Writer (Person 2) -> result dict (Person 3 renders it).

Plug-in behavior:
  - If a top-level `extractor.py` exists exporting `extract(source_text, source_label=...)`,
    it's used. Otherwise falls back to mock_pipeline.mock_extract.
  - If a top-level `writer.py` exists exporting `enrich(raw_endpoints, source_label=...)`,
    it's used. Otherwise falls back to mock_pipeline.mock_enrich.

This means Person 1 and Person 2 can each drop a single file into the repo root
matching those function names and the whole app switches from mock to real data
with zero changes here.
"""
import json
import importlib
import datetime
from pathlib import Path

from mock_pipeline import mock_extract, mock_enrich

CACHE_DIR = Path(__file__).parent / ".run_cache"
CACHE_DIR.mkdir(exist_ok=True)
LAST_RUN_FILE = CACHE_DIR / "last_run.json"


def _load_real_or_mock(module_name, func_name, mock_func):
    try:
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        return func, True
    except (ImportError, AttributeError):
        return mock_func, False


def _diff_summary(old_endpoints, new_endpoints):
    if old_endpoints is None:
        return None
    old_keys = {(e["method"], e["path"]) for e in old_endpoints}
    new_keys = {(e["method"], e["path"]) for e in new_endpoints}
    added = new_keys - old_keys
    removed = old_keys - new_keys
    parts = []
    if added:
        parts.append(f"{len(added)} endpoint(s) added: " +
                     ", ".join(f"{m} {p}" for m, p in sorted(added)))
    if removed:
        parts.append(f"{len(removed)} endpoint(s) removed: " +
                     ", ".join(f"{m} {p}" for m, p in sorted(removed)))
    if not parts:
        parts.append("No endpoint additions/removals detected (descriptions may still differ).")
    return " ".join(parts)


def run(source_text: str, source_label: str = "input") -> dict:
    extract_fn, extractor_is_real = _load_real_or_mock("extractor", "extract", mock_extract)
    enrich_fn, writer_is_real = _load_real_or_mock("writer", "enrich", mock_enrich)

    raw_endpoints = extract_fn(source_text, source_label=source_label)
    enriched = enrich_fn(raw_endpoints, source_label=source_label)

    old_endpoints = None
    if LAST_RUN_FILE.exists():
        try:
            old_endpoints = json.loads(LAST_RUN_FILE.read_text()).get("endpoints")
        except Exception:
            old_endpoints = None

    scores = [e.get("eval_score", {}).get("avg") for e in enriched if e.get("eval_score")]
    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    result = {
        "meta": {
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "source_name": source_label,
            "diff_summary": _diff_summary(old_endpoints, enriched),
            "avg_eval_score": avg_score,
            "extractor_is_real": extractor_is_real,
            "writer_is_real": writer_is_real,
        },
        "endpoints": enriched,
    }

    LAST_RUN_FILE.write_text(json.dumps(result, indent=2))
    return result
