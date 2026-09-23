"""
JavaScript Parser — Extracts API endpoints from Express.js code.
Uses regex-based parsing since we can't use a JS AST parser in Python easily.
Enhanced with multi-pattern matching for robustness.
"""

import re
from typing import Optional


def detect_js_framework(code: str) -> str:
    """Detect JavaScript framework."""
    if "express()" in code.lower() or "require('express')" in code or 'require("express")' in code:
        return "express"
    if "import express" in code or "from 'express'" in code:
        return "express"
    if "Koa()" in code or "require('koa')" in code:
        return "koa"
    if "Hono()" in code or "require('hono')" in code:
        return "hono"
    return "express"


def _find_router_variables(code: str) -> dict:
    """Find Express Router variables and detect potential prefixes."""
    routers = {}
    # Pattern: const userRouter = express.Router()
    router_pattern = re.compile(
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:express\.Router\(\)|Router\(\))',
        re.MULTILINE
    )
    for match in router_pattern.finditer(code):
        routers[match.group(1)] = ""

    # Try to find app.use("/prefix", routerVar)
    use_pattern = re.compile(
        r'app\.use\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)\s*\)',
        re.MULTILINE
    )
    for match in use_pattern.finditer(code):
        prefix = match.group(1)
        var_name = match.group(2)
        if var_name in routers:
            routers[var_name] = prefix

    return routers


def _extract_js_params(path: str) -> list[dict]:
    """Extract path parameters from Express-style routes."""
    params = []
    param_pattern = re.compile(r':(\w+)')
    for match in param_pattern.finditer(path):
        params.append({
            "name": match.group(1),
            "type": "string",
            "required": True,
            "location": "path"
        })
    return params


def _extract_function_body_hints(body: str) -> dict:
    """Extract hints from function body about request handling."""
    hints = {}

    if "req.body" in body:
        hints["request_body"] = {"type": "json"}
    if "req.query" in body:
        hints["has_query_params"] = True
    if "req.params" in body:
        hints["has_path_params"] = True
    if "req.file" in body or "req.files" in body:
        hints["request_body"] = {"type": "multipart"}

    # Try to extract query param names
    query_params = re.findall(r'req\.query\.(\w+)', body)
    if query_params:
        hints["query_params"] = [{"name": p, "type": "string", "required": False, "location": "query"} for p in set(query_params)]

    # Try to extract body field names
    body_fields = re.findall(r'req\.body\.(\w+)', body)
    destructured = re.findall(r'{\s*([^}]+)\s*}\s*=\s*req\.body', body)
    if destructured:
        for d in destructured:
            body_fields.extend([f.strip() for f in d.split(",")])
    if body_fields:
        hints["body_fields"] = list(set(body_fields))

    return hints


def parse_js_code(code: str, framework: str = "auto") -> dict:
    """Parse JavaScript API code and extract endpoint information."""

    if framework == "auto":
        framework = detect_js_framework(code)

    routers = _find_router_variables(code)
    app_vars = {"app"} | set(routers.keys())

    # Also find: const app = express()
    app_pattern = re.compile(r'(?:const|let|var)\s+(\w+)\s*=\s*express\(\)', re.MULTILINE)
    for match in app_pattern.finditer(code):
        app_vars.add(match.group(1))

    endpoints = []
    methods = ["get", "post", "put", "delete", "patch", "head", "options"]

    # Build regex pattern for all app vars and methods
    vars_pattern = "|".join(re.escape(v) for v in app_vars)
    methods_pattern = "|".join(methods)

    # Pattern: app.get("/path", (req, res) => { ... }) or app.get("/path", handler)
    route_pattern = re.compile(
        rf'(?P<var>{vars_pattern})\.(?P<method>{methods_pattern})\(\s*["\'](?P<path>[^"\']+)["\']',
        re.MULTILINE | re.IGNORECASE
    )

    # Find all route definitions
    for match in route_pattern.finditer(code):
        var_name = match.group("var")
        method = match.group("method").upper()
        path = match.group("path")

        # Apply router prefix
        prefix = routers.get(var_name, "")
        if prefix:
            path = prefix.rstrip("/") + "/" + path.lstrip("/")

        # Extract path params
        params = _extract_js_params(path)

        # Try to find the function body for hints
        start_pos = match.end()
        body_hints = {}

        # Find the matching closing bracket/paren
        brace_count = 0
        body_start = code.find("{", start_pos)
        if body_start != -1:
            body_end = body_start
            for i in range(body_start, min(body_start + 2000, len(code))):
                if code[i] == "{":
                    brace_count += 1
                elif code[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        body_end = i
                        break
            body = code[body_start:body_end + 1]
            body_hints = _extract_function_body_hints(body)

        # Add query params from hints
        if "query_params" in body_hints:
            params.extend(body_hints["query_params"])

        # Try to find inline comments or JSDoc
        line_start = code.rfind("\n", 0, match.start())
        preceding_lines = code[max(0, line_start - 300):match.start()]
        comment_match = re.search(r'//\s*(.+)$', preceding_lines, re.MULTILINE)
        jsdoc_match = re.search(r'/\*\*\s*([\s\S]*?)\*/', preceding_lines)

        docstring = None
        if jsdoc_match:
            docstring = jsdoc_match.group(1).strip()
            docstring = re.sub(r'\n\s*\*\s*', '\n', docstring).strip()
        elif comment_match:
            docstring = comment_match.group(1).strip()

        # Find the line number
        line_number = code[:match.start()].count("\n") + 1

        endpoint = {
            "path": path,
            "method": method,
            "function_name": f"{method.lower()}_{path.replace('/', '_').strip('_')}",
            "parameters": params,
            "docstring": docstring,
            "request_body": body_hints.get("request_body"),
            "body_fields": body_hints.get("body_fields", []),
            "line_number": line_number,
        }
        endpoints.append(endpoint)

    return {
        "endpoints": endpoints,
        "framework_detected": framework,
        "language": "javascript",
        "total_endpoints": len(endpoints),
    }
