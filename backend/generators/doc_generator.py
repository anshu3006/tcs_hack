"""
AI-Powered Documentation Generator — Uses Gemini to generate beautiful API docs.
Also generates OpenAPI specs from parsed endpoint data.
"""

import os
import json
from typing import Optional

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def _get_gemini_model():
    """Initialize and return Gemini model."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or not HAS_GEMINI:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


def generate_docs_with_ai(endpoints: list[dict], code: str, style: str = "stripe") -> str:
    """Generate beautiful API documentation using Gemini AI."""
    
    model = _get_gemini_model()

    style_instructions = {
        "stripe": "Write in the style of Stripe's API documentation — concise, professional, with clear examples. Use tables for parameters.",
        "minimal": "Write minimal documentation with just the essentials — endpoint, method, parameters, and one example.",
        "detailed": "Write comprehensive documentation with detailed descriptions, multiple examples, error handling info, and best practices.",
    }

    prompt = f"""You are an expert API documentation writer. Generate clear, beautiful API documentation in Markdown format.

{style_instructions.get(style, style_instructions["stripe"])}

## Parsed Endpoints Data:
```json
{json.dumps(endpoints, indent=2)}
```

## Original Source Code (for context):
```
{code[:3000]}
```

## Instructions:
1. Start with a brief API Overview section
2. For each endpoint, document:
   - HTTP Method and Path (as a heading)
   - Brief description of what it does
   - Parameters table (Name | Type | Required | Location | Description)
   - Request body schema (if applicable)
   - Example request (curl command)
   - Example response (JSON)
   - Possible error codes
3. Add a "Quick Start" section at the top with the most common use case
4. Use proper markdown formatting with code blocks
5. Be concise but complete
6. Make the documentation feel premium and professional

Generate the documentation now:"""

    if model:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return _generate_fallback_docs(endpoints, code)
    else:
        return _generate_fallback_docs(endpoints, code)


def _generate_fallback_docs(endpoints: list[dict], code: str = "") -> str:
    """Generate documentation without AI — rule-based fallback."""
    
    lines = ["# API Documentation\n"]
    lines.append("## Quick Start\n")
    
    if endpoints:
        ep = endpoints[0]
        lines.append(f"```bash")
        lines.append(f'curl -X {ep["method"]} http://localhost:5000{ep["path"]}')
        lines.append(f"```\n")
    
    lines.append("---\n")
    lines.append("## Endpoints\n")
    
    for ep in endpoints:
        method = ep.get("method", "GET")
        path = ep.get("path", "/")
        func_name = ep.get("function_name", "unknown")
        docstring = ep.get("docstring", "")
        params = ep.get("parameters", [])
        body = ep.get("request_body")
        body_fields = ep.get("body_fields", [])
        
        # Heading
        lines.append(f"### `{method}` {path}\n")
        
        # Description
        if docstring:
            lines.append(f"{docstring}\n")
        else:
            # Generate description from function name
            desc = func_name.replace("_", " ").title()
            lines.append(f"{desc}\n")
        
        # Parameters table
        if params:
            lines.append("| Parameter | Type | Required | Location | Description |")
            lines.append("|-----------|------|----------|----------|-------------|")
            for p in params:
                name = p.get("name", "?")
                ptype = p.get("type", "string")
                req = "✅" if p.get("required", True) else "❌"
                loc = p.get("location", "query")
                desc = p.get("description", "-")
                lines.append(f"| `{name}` | `{ptype}` | {req} | {loc} | {desc} |")
            lines.append("")
        
        # Request body
        if body or body_fields:
            lines.append("**Request Body** (`application/json`):\n")
            if body_fields:
                lines.append("```json")
                body_obj = {f: "<value>" for f in body_fields}
                lines.append(json.dumps(body_obj, indent=2))
                lines.append("```\n")
            elif body and body.get("model"):
                lines.append(f"Schema: `{body['model']}`\n")
        
        # Example request
        lines.append("**Example Request:**\n")
        curl_parts = [f'curl -X {method} http://localhost:5000{path}']
        if method in ("POST", "PUT", "PATCH"):
            curl_parts.append('  -H "Content-Type: application/json"')
            if body_fields:
                body_obj = {f: "example" for f in body_fields}
                curl_parts.append(f"  -d '{json.dumps(body_obj)}'")
        lines.append("```bash")
        lines.append(" \\\n".join(curl_parts))
        lines.append("```\n")
        
        # Example response
        lines.append("**Example Response:**\n")
        lines.append("```json")
        lines.append(json.dumps({"status": "success", "message": f"{func_name} completed"}, indent=2))
        lines.append("```\n")
        
        lines.append("---\n")
    
    return "\n".join(lines)


def generate_openapi_spec(endpoints: list[dict], title: str = "API", version: str = "1.0.0") -> dict:
    """Generate an OpenAPI 3.0 specification from parsed endpoints."""
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": title,
            "version": version,
            "description": f"Auto-generated API specification with {len(endpoints)} endpoints"
        },
        "paths": {},
        "components": {
            "schemas": {}
        }
    }
    
    for ep in endpoints:
        path = ep.get("path", "/")
        method = ep.get("method", "GET").lower()
        func_name = ep.get("function_name", "unknown")
        params = ep.get("parameters", [])
        docstring = ep.get("docstring", "")
        body = ep.get("request_body")
        body_fields = ep.get("body_fields", [])
        
        if path not in spec["paths"]:
            spec["paths"][path] = {}
        
        operation = {
            "operationId": func_name,
            "summary": docstring or func_name.replace("_", " ").title(),
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                },
                "400": {"description": "Bad request"},
                "404": {"description": "Not found"},
                "500": {"description": "Internal server error"}
            }
        }
        
        for p in params:
            operation["parameters"].append({
                "name": p.get("name", "param"),
                "in": p.get("location", "query"),
                "required": p.get("required", False),
                "schema": {"type": p.get("type", "string")},
                "description": p.get("description", "")
            })
        
        if method in ("post", "put", "patch") and (body or body_fields):
            properties = {}
            if body_fields:
                for f in body_fields:
                    properties[f] = {"type": "string"}
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": properties
                        }
                    }
                }
            }

        spec["paths"][path][method] = operation
    
    return spec
