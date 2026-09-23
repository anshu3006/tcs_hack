"""
Self-eval against the 80% clarity/completeness target.

Runs a second LLM pass (rubric prompt, temperature 0 for consistency) that
scores each generated doc 1-5 on clarity and completeness, then aggregates
so the demo can cite a real number ("avg 4.2/5 across 18 endpoints") instead
of a vague claim. 4.0/5 is treated as the 80% bar.
"""
import json
from typing import Dict, List

from .llm_client import LLMError, call_llm
from .prompts import EVAL_SYSTEM, build_eval_prompt


def _parse(text: str) -> dict:
    text = text.strip().strip("`")
    if text.startswith("json"):
        text = text[4:]
    return json.loads(text)


def score_doc(endpoint: dict, doc: dict, provider: str = "gemini") -> dict:
    if doc.get("error"):
        return {
            "endpoint_id": doc.get("endpoint_id"),
            "clarity": None,
            "completeness": None,
            "rationale": "skipped - generation failed",
        }

    prompt = build_eval_prompt(endpoint, doc)
    try:
        raw = call_llm(prompt, provider=provider, system=EVAL_SYSTEM, temperature=0.0)
        result = _parse(raw)
    except (LLMError, json.JSONDecodeError) as e:
        result = {"clarity": None, "completeness": None, "rationale": f"eval failed: {e}"}

    result["endpoint_id"] = doc.get("endpoint_id")
    return result


def score_all(endpoints: List[Dict], docs: List[Dict], provider: str = "gemini") -> Dict:
    by_id = {(e.get("id") or f"{e.get('method')}_{e.get('path')}"): e for e in endpoints}
    scores = [score_doc(by_id.get(d.get("endpoint_id"), {}), d, provider=provider) for d in docs]

    clarity_vals = [s["clarity"] for s in scores if s.get("clarity") is not None]
    completeness_vals = [s["completeness"] for s in scores if s.get("completeness") is not None]
    avg_clarity = round(sum(clarity_vals) / len(clarity_vals), 2) if clarity_vals else None
    avg_completeness = (
        round(sum(completeness_vals) / len(completeness_vals), 2) if completeness_vals else None
    )
    overall = (
        round((avg_clarity + avg_completeness) / 2, 2)
        if avg_clarity is not None and avg_completeness is not None
        else None
    )
    meets_target = overall is not None and overall >= 4.0  # 4/5 == 80%

    return {
        "per_endpoint": scores,
        "n_scored": len(clarity_vals),
        "n_total": len(docs),
        "avg_clarity": avg_clarity,
        "avg_completeness": avg_completeness,
        "overall_avg": overall,
        "meets_80pct_target": meets_target,
    }
