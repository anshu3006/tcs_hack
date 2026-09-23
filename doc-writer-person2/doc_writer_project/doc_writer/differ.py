"""
Diffing: summarize what changed between two generation runs in plain English.

Structural diff (added/removed/changed endpoint ids) is computed locally with
no LLM call. For endpoints whose doc actually changed, one LLM call per
changed endpoint produces a short plain-English summary of what a developer
reading the docs would notice.
"""
import json
from typing import Dict, List

from .llm_client import LLMError, call_llm
from .prompts import build_diff_summary_prompt


def _index(docs: List[Dict]) -> Dict[str, Dict]:
    return {d.get("endpoint_id"): d for d in docs}


def _strip(doc: Dict) -> Dict:
    return {k: v for k, v in doc.items() if k != "_cache_hit"}


def structural_diff(old_docs: List[Dict], new_docs: List[Dict]) -> Dict:
    old_ix, new_ix = _index(old_docs), _index(new_docs)
    added = [k for k in new_ix if k not in old_ix]
    removed = [k for k in old_ix if k not in new_ix]
    changed = [k for k in new_ix if k in old_ix and _strip(old_ix[k]) != _strip(new_ix[k])]
    unchanged = [k for k in new_ix if k in old_ix and k not in changed]
    return {"added": added, "removed": removed, "changed": changed, "unchanged": unchanged}


def summarize_changes(old_docs: List[Dict], new_docs: List[Dict], provider: str = "gemini") -> Dict:
    """Structural diff + a plain-English summary per changed/added/removed endpoint."""
    diff = structural_diff(old_docs, new_docs)
    old_ix, new_ix = _index(old_docs), _index(new_docs)
    summaries: Dict[str, str] = {}

    for eid in diff["changed"]:
        try:
            raw = call_llm(
                build_diff_summary_prompt(eid, old_ix[eid], new_ix[eid]),
                provider=provider,
                temperature=0.0,
            )
            text = raw.strip().strip("`")
            text = text[4:] if text.startswith("json") else text
            summaries[eid] = json.loads(text).get("summary", raw)
        except (LLMError, json.JSONDecodeError, ValueError) as e:
            summaries[eid] = f"[diff summary unavailable: {e}]"

    for eid in diff["added"]:
        summaries[eid] = "New endpoint - documentation added."
    for eid in diff["removed"]:
        summaries[eid] = "Endpoint removed from the API."

    diff["summaries"] = summaries
    return diff
