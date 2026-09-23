"""
OpenAPI/Swagger Parser — Parses YAML/JSON OpenAPI specs.
"""

import json
import yaml
from typing import Optional


def parse_openapi_spec(content: str) -> dict:
    """Parse an OpenAPI specification from YAML or JSON string."""
    
    # Try JSON first, then YAML
    spec = None
    try:
        spec = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        try:
            spec = yaml.safe_load(content)
        except yaml.YAMLError:
            return {
                "endpoints": [],
                "framework_detected": "openapi",
                "language": "openapi",
                "total_endpoints": 0,
                "error": "Could not parse as JSON or YAML"
            }

    if not spec or not isinstance(spec, dict):
        return {
            "endpoints": [],
            "framework_detected": "openapi",
            "language": "openapi",
            "total_endpoints": 0,
            "error": "Invalid spec format"
        }

    endpoints = []
    paths = spec.get("paths", {})
    
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
            
        for method, operation in path_item.items():
            if method.lower() in ("get", "post", "put", "delete", "patch", "head", "options"):
                if not isinstance(operation, dict):
                    continue
                    
                params = []
                
                # Extract parameters
                for param in operation.get("parameters", []):
                    if isinstance(param, dict):
                        params.append({
                            "name": param.get("name", "unknown"),
                            "type": param.get("schema", {}).get("type", "string") if isinstance(param.get("schema"), dict) else "string",
                            "required": param.get("required", False),
                            "location": param.get("in", "query"),
                            "description": param.get("description", ""),
                        })
                
                # Extract request body
                request_body = None
                rb = operation.get("requestBody", {})
                if isinstance(rb, dict):
                    content_types = rb.get("content", {})
                    if isinstance(content_types, dict):
                        for ct, ct_info in content_types.items():
                            if isinstance(ct_info, dict) and "schema" in ct_info:
                                request_body = {
                                    "type": ct,
                                    "schema": ct_info["schema"]
                                }
                                break

                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "function_name": operation.get("operationId", f"{method}_{path}"),
                    "parameters": params,
                    "docstring": operation.get("summary", "") or operation.get("description", ""),
                    "request_body": request_body,
                    "responses": operation.get("responses", {}),
                    "tags": operation.get("tags", []),
                    "line_number": 0,
                }
                endpoints.append(endpoint)

    return {
        "endpoints": endpoints,
        "framework_detected": "openapi",
        "language": "openapi",
        "total_endpoints": len(endpoints),
        "info": spec.get("info", {}),
        "servers": spec.get("servers", []),
    }
