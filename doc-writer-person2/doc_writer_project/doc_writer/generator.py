"""
Person 2 core: JSON schema (from Person 1) -> enriched per-endpoint documentation.

Consumes ONLY Person 1's JSON (see schema.py for the contract) - this module
never touches source code or OpenAPI files directly.
"""
import json
from typing import Dict, List

from . import cache
from .llm_client import LLMError, call_llm
from .prompts import GENERATION_SYSTEM, PROMPT_VERSION, build_generation_prompt


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _endpoint_id(endpoint: dict) -> str:
    return endpoint.get("id") or f"{endpoint.get('method', '?')}_{endpoint.get('path', '?')}"


def generate_endpoint_doc(endpoint: dict, provider: str = "gemini", use_cache: bool = True) -> dict:
    """Generate enriched docs for a single endpoint dict (Person 1's schema)."""
    key = cache.endpoint_hash(endpoint, PROMPT_VERSION)

    if use_cache:
        cached = cache.get(key)
        if cached is not None:
            cached["_cache_hit"] = True
            return cached

    prompt = build_generation_prompt(endpoint)
    raw = call_llm(prompt, provider=provider, system=GENERATION_SYSTEM)

    try:
        doc = _parse_json_response(raw)
    except json.JSONDecodeError:
        # Degrade gracefully instead of dropping the endpoint entirely.
        doc = {
            "description": raw.strip()[:500],
            "parameters": [],
            "request_example": None,
            "response_example": None,
            "edge_cases": ["[generator] LLM did not return valid JSON; raw text kept as description"],
        }

    doc["endpoint_id"] = _endpoint_id(endpoint)
    doc["prompt_version"] = PROMPT_VERSION
    doc["_cache_hit"] = False

    if use_cache:
        cache.set(key, doc)
    return doc


def generate_all(schema: dict, provider: str = "gemini", use_cache: bool = True) -> List[Dict]:
    """schema: Person 1's output, shaped {"api_name": ..., "endpoints": [...]}."""
    docs = []
    for ep in schema.get("endpoints", []):
        try:
            docs.append(generate_endpoint_doc(ep, provider=provider, use_cache=use_cache))
        except LLMError as e:
            docs.append(
                {
                    "endpoint_id": _endpoint_id(ep),
                    "error": str(e),
                    "description": None,
                    "parameters": [],
                    "request_example": None,
                    "response_example": None,
                    "edge_cases": [],
                }
            )
    return docs
