"""
Prompt templates for generation, self-eval, and diff summarization.

Bump PROMPT_VERSION any time a template's wording changes meaningfully, and
log the change (with a before/after example) in PROMPTS.md at the repo root.
PROMPT_VERSION is also mixed into the cache key, so a version bump correctly
invalidates cached docs generated under the old wording.
"""
import json

PROMPT_VERSION = "v1"

GENERATION_SYSTEM = (
    "You are a precise technical writer generating API documentation for developers. "
    "Only state what is supported by the given endpoint data - never invent parameters, "
    "fields, or behavior that isn't present in the input. If something is ambiguous, say so "
    "briefly instead of guessing. Respond with ONLY valid JSON, no markdown fences, no preamble."
)

EVAL_SYSTEM = (
    "You are a strict reviewer scoring API documentation for clarity and completeness. "
    "Be honest and consistent - most first-draft docs score 3-4, not 5. "
    "Respond with ONLY valid JSON, no markdown fences, no preamble."
)


def _json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def build_generation_prompt(endpoint: dict) -> str:
    return f"""Generate documentation for this API endpoint. Input data (from static analysis / OpenAPI spec):

{_json(endpoint)}

Return a single JSON object with exactly these keys:
- "description": 1-3 sentence plain-English summary of what this endpoint does
- "parameters": array of {{"name", "explanation"}} - one entry per input parameter, explaining purpose and constraints in plain English (empty array if none)
- "request_example": a realistic example request body/params for this endpoint, as a string, or null if the endpoint takes no input
- "response_example": a realistic example success response, as a string
- "edge_cases": array of short strings describing notable edge cases, error conditions, or gotchas a consumer should know (based only on what's in the input data - e.g. required params, status codes present)

Return ONLY the JSON object."""


def build_eval_prompt(endpoint: dict, generated_doc: dict) -> str:
    return f"""Score this generated API documentation against the source endpoint data.

SOURCE ENDPOINT DATA:
{_json(endpoint)}

GENERATED DOCUMENTATION:
{_json(generated_doc)}

Score 1-5 (5 = excellent) on:
- "clarity": is it easy for a developer to understand?
- "completeness": does it cover all parameters/responses present in the source data?

Return ONLY a JSON object: {{"clarity": <1-5>, "completeness": <1-5>, "rationale": "<one sentence>"}}"""


def build_diff_summary_prompt(endpoint_id: str, old_doc: dict, new_doc: dict) -> str:
    return f"""Two versions of generated documentation exist for endpoint "{endpoint_id}". Summarize in 1-3 plain-English sentences what meaningfully changed for a developer reading the docs (ignore trivial rewording; focus on added/removed/changed information).

OLD:
{_json(old_doc)}

NEW:
{_json(new_doc)}

Return ONLY a JSON object: {{"summary": "<your summary>"}}"""
