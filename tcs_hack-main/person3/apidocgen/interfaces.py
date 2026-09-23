"""
Shared contract between the three pipeline stages.

Person 1 (Extractor)  -> produces a list of RAW endpoint dicts (see RAW_ENDPOINT_SHAPE)
Person 2 (Writer)     -> consumes raw endpoints, returns ENRICHED endpoint dicts
Person 3 (UI/CLI)     -> consumes enriched endpoints, renders them

Everyone only needs to agree on these two dict shapes. As long as Person 1's
extractor and Person 2's writer functions match the signatures below, they can
be dropped into this repo and orchestrator.py will pick them up automatically
(see ORCHESTRATOR PLUG-IN section at the bottom).
"""

# ---------------------------------------------------------------------------
# RAW_ENDPOINT_SHAPE — what extractor.extract(source) must return per endpoint
# ---------------------------------------------------------------------------
RAW_ENDPOINT_SHAPE = {
    "method": "GET",                # HTTP verb, uppercase
    "path": "/users/{id}",          # route template
    "summary": "",                  # short line, may be empty if unknown
    "parameters": [
        {"name": "id", "in": "path", "type": "integer", "required": True}
    ],
    "request_body": None,           # dict schema or None
    "responses": {                  # keyed by status code
        "200": {"description": "", "schema": {}}
    },
    "source": "openapi",            # "openapi" | "python-ast" | other
}

# ---------------------------------------------------------------------------
# ENRICHED_ENDPOINT_SHAPE — what writer.enrich(raw_endpoints) must add
# ---------------------------------------------------------------------------
# Enriched endpoint = RAW_ENDPOINT_SHAPE fields + these additional keys:
ENRICHED_EXTRA_KEYS = {
    "description": "Generated plain-English description of the endpoint.",
    "parameter_explanations": {"id": "Explanation of what this param does."},
    "examples": {
        "request": {},
        "response": {},
    },
    "edge_cases": ["List of edge-case notes, plain English."],
    "eval_score": {"clarity": 4, "completeness": 5, "avg": 4.5},
}

# ---------------------------------------------------------------------------
# PIPELINE_RESULT_SHAPE — what orchestrator.run() returns to the UI/CLI
# ---------------------------------------------------------------------------
PIPELINE_RESULT_SHAPE = {
    "meta": {
        "generated_at": "ISO timestamp",
        "source_name": "uploaded-file-or-label",
        "diff_summary": "Plain-English summary of what changed vs last run, or None",
        "avg_eval_score": 4.3,
    },
    "endpoints": [],  # list of enriched endpoint dicts
}
