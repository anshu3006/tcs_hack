"""
Stand-in implementations of Person 1's extractor and Person 2's writer,
used until their real modules land. Realistic enough to build/demo the
full UI now. Swap-out happens automatically in orchestrator.py once
extractor.py / writer.py exist with matching function names.
"""
import re
import random

_SAMPLE_ENDPOINTS = [
    {"method": "GET", "path": "/users", "params": [("page", "integer", False)]},
    {"method": "GET", "path": "/users/{id}", "params": [("id", "integer", True)]},
    {"method": "POST", "path": "/users", "params": [("body", "object", True)]},
    {"method": "DELETE", "path": "/users/{id}", "params": [("id", "integer", True)]},
    {"method": "GET", "path": "/orders/{id}/items", "params": [("id", "integer", True)]},
]


def mock_extract(source_text: str, source_label: str = "pasted-input"):
    """Fake 'extraction': if it looks like OpenAPI JSON/YAML, or Python route
    decorators, we still just hand back the sample set (varied methods/paths)
    so the UI has something real-shaped to render, regardless of input."""
    looks_openapi = bool(re.search(r'"paths"\s*:|^paths:', source_text or "", re.M))
    endpoints = []
    for e in _SAMPLE_ENDPOINTS:
        endpoints.append({
            "method": e["method"],
            "path": e["path"],
            "summary": "",
            "parameters": [
                {"name": n, "in": "path" if "{" + n + "}" in e["path"] else "query",
                 "type": t, "required": r}
                for (n, t, r) in e["params"]
            ],
            "request_body": {"type": "object"} if e["method"] == "POST" else None,
            "responses": {"200": {"description": "Successful response", "schema": {}}},
            "source": "openapi" if looks_openapi else "python-ast",
        })
    return endpoints


def mock_enrich(raw_endpoints, source_label: str = "pasted-input"):
    """Fake 'LLM enrichment': deterministic-ish text so demos are reproducible."""
    enriched = []
    for ep in raw_endpoints:
        clarity = random.randint(3, 5)
        completeness = random.randint(3, 5)
        enriched.append({
            **ep,
            "description": f"{ep['method']} {ep['path']} — handles {ep['method'].lower()} "
                            f"operations for this resource.",
            "parameter_explanations": {
                p["name"]: f"The {p['name']} {'(required) ' if p['required'] else ''}"
                           f"{p['type']} value for this request."
                for p in ep["parameters"]
            },
            "examples": {
                "request": {"example": True},
                "response": {"status": 200, "body": {"example": True}},
            },
            "edge_cases": [
                f"Returns 404 if the referenced resource does not exist."
                if "{" in ep["path"] else "Empty result set returns an empty list, not an error."
            ],
            "eval_score": {
                "clarity": clarity,
                "completeness": completeness,
                "avg": round((clarity + completeness) / 2, 1),
            },
        })
    return enriched
