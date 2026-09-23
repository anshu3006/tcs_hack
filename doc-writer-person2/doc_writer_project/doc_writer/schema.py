"""
Shared contract between Person 1 (Extractor) and Person 2 (Doc Writer).

This is the JSON shape Person 1's extractor must produce and everything in
this package consumes. Share EXTRACTOR_SCHEMA with Person 1 early - it's the
interface between PC1 and PC2, and the thing Person 3's orchestrator passes
through unchanged.
"""

EXTRACTOR_SCHEMA = {
    "type": "object",
    "required": ["api_name", "endpoints"],
    "properties": {
        "api_name": {"type": "string"},
        "version": {"type": "string"},
        "source": {
            "type": "string",
            "description": "e.g. 'openapi', 'flask-ast', 'fastapi-ast', 'spring'",
        },
        "endpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["method", "path"],
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "stable id, e.g. 'GET_/users/{id}'. "
                        "Generator falls back to '<method>_<path>' if absent.",
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    },
                    "path": {"type": "string"},
                    "summary": {
                        "type": "string",
                        "description": "existing docstring/comment if any - useful for eval parity checks",
                    },
                    "parameters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "in": {
                                    "type": "string",
                                    "enum": ["path", "query", "body", "header"],
                                },
                                "type": {"type": "string"},
                                "required": {"type": "boolean"},
                                "description": {"type": "string"},
                            },
                        },
                    },
                    "request_body": {"type": ["object", "null"]},
                    "responses": {
                        "type": "object",
                        "description": "keyed by status code, e.g. {'200': {...}, '404': {...}}",
                    },
                    "source_location": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string"},
                            "line": {"type": "integer"},
                        },
                    },
                },
            },
        },
    },
}


def validate_minimal(schema: dict) -> list:
    """Cheap structural check with no external deps.

    Returns a list of problem strings; empty list means it's usable.
    Run this on whatever Person 1 hands off before generating docs from it.
    """
    problems = []
    if "endpoints" not in schema:
        problems.append("missing top-level 'endpoints' key")
        return problems
    if not isinstance(schema["endpoints"], list):
        problems.append("'endpoints' must be a list")
        return problems
    for i, ep in enumerate(schema["endpoints"]):
        for req in ("method", "path"):
            if req not in ep:
                problems.append(f"endpoints[{i}] missing required '{req}'")
    return problems
