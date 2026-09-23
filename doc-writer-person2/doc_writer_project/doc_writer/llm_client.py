"""
call_llm() abstraction - the one place in this module that talks to an LLM.

Primary provider : Google Gemini REST API (gemini-2.5-flash by default).
Backup provider   : OpenRouter (OpenAI-compatible chat/completions API) -
                     covers OpenAI models too, just point OPENROUTER_MODEL
                     at e.g. "openai/gpt-4o-mini".
Offline provider  : "mock" - deterministic canned JSON, no network or key
                     needed. Use this for local dev / if wifi at the venue
                     is unreliable during the demo.

Usage:
    from doc_writer.llm_client import call_llm
    text = call_llm("Explain this endpoint...", provider="gemini")

call_llm() will automatically fall back to `fallback` (default "openrouter")
if the primary provider errors out, so a single flaky call doesn't kill a
whole generation run.
"""
import os
import time
from typing import Optional

import requests

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    """Raised when a provider call fails (bad key, network, bad response shape)."""


def _call_gemini(prompt, system=None, temperature=0.3, max_tokens=2048, timeout=30, **_):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMError("GEMINI_API_KEY not set")

    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}

    resp = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        json=body,
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise LLMError(f"Gemini {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected Gemini response shape: {e} / {data}") from e


def _call_openrouter(prompt, system=None, temperature=0.3, max_tokens=2048, timeout=30, **_):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMError("OPENROUTER_API_KEY not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        raise LLMError(f"OpenRouter {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected OpenRouter response shape: {e} / {data}") from e


def _call_mock(prompt, system=None, **_):
    """Deterministic offline responses. Shape-matches whichever prompt type is
    calling (generation / eval / diff) so the whole pipeline - not just
    generation - is demoable with zero API keys."""
    import json

    if system and "reviewer scoring" in system:
        return json.dumps({"clarity": 4, "completeness": 4, "rationale": "[MOCK] offline placeholder score"})
    if "meaningfully changed" in prompt:
        return json.dumps({"summary": "[MOCK] offline placeholder diff summary"})
    return json.dumps(
        {
            "description": "[MOCK] Placeholder description - no LLM key configured.",
            "parameters": [],
            "request_example": "{}",
            "response_example": "{}",
            "edge_cases": ["[MOCK] running offline; set GEMINI_API_KEY for real output"],
        }
    )


_PROVIDERS = {"gemini": _call_gemini, "openrouter": _call_openrouter, "mock": _call_mock}


def call_llm(
    prompt: str,
    provider: str = "gemini",
    system: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    retries: int = 2,
    fallback: Optional[str] = "openrouter",
) -> str:
    """Call `provider`; on failure, retry `retries` times, then try `fallback` once.

    Raises LLMError if every attempt across both providers fails.
    """
    order = [provider] + ([fallback] if fallback and fallback != provider else [])
    last_err: Optional[LLMError] = None

    for p in order:
        fn = _PROVIDERS.get(p)
        if fn is None:
            last_err = LLMError(f"Unknown provider '{p}'")
            continue
        for attempt in range(retries):
            try:
                return fn(prompt, system=system, temperature=temperature, max_tokens=max_tokens)
            except LLMError as e:
                last_err = e
                time.sleep(0.5 * (attempt + 1))

    raise last_err or LLMError("All providers failed")
