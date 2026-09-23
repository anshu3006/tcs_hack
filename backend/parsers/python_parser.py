"""
Python AST Parser — Extracts API endpoints from Flask and FastAPI code.
Uses proper AST analysis, NOT regex. This is a key differentiator.
"""

import ast
import re
from typing import Optional


FLASK_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
FASTAPI_METHODS = FLASK_METHODS


def detect_framework(code: str) -> str:
    """Detect if the code uses Flask or FastAPI."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "fastapi" in node.module.lower():
                return "fastapi"
            if node.module and "flask" in node.module.lower():
                return "flask"
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "fastapi" in alias.name.lower():
                    return "fastapi"
                if "flask" in alias.name.lower():
                    return "flask"
    # Fallback: check for common patterns
    if "FastAPI()" in code:
        return "fastapi"
    if "Flask(" in code:
        return "flask"
    return "flask"  # default


def _extract_docstring(node: ast.FunctionDef) -> Optional[str]:
    """Extract docstring from a function definition."""
    if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, (ast.Constant, ast.Str))):
        val = node.body[0].value
        if isinstance(val, ast.Constant):
            return str(val.value)
        return val.s
    return None


def _extract_parameters(node: ast.FunctionDef, framework: str) -> list[dict]:
    """Extract function parameters with type annotations."""
    params = []
    for arg in node.args.args:
        if arg.arg in ("self", "cls"):
            continue
        param = {
            "name": arg.arg,
            "type": "any",
            "required": True,
            "location": "path"
        }
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                param["type"] = arg.annotation.id
            elif isinstance(arg.annotation, ast.Constant):
                param["type"] = str(arg.annotation.value)
            elif isinstance(arg.annotation, ast.Attribute):
                param["type"] = ast.dump(arg.annotation)

        # FastAPI-specific: skip Request, Response, Depends, etc.
        if framework == "fastapi" and param["type"] in ("Request", "Response", "BackgroundTasks"):
            continue
        # Skip common non-parameter args
        if param["name"] in ("request", "response", "db", "session"):
            param["location"] = "internal"

        params.append(param)

    # Check for defaults (optional params)
    defaults = node.args.defaults
    if defaults:
        num_required = len(node.args.args) - len(defaults)
        for i, p in enumerate(params):
            if i >= num_required:
                p["required"] = False

    return [p for p in params if p.get("location") != "internal"]


def _extract_request_body(node: ast.FunctionDef) -> Optional[dict]:
    """Try to detect request body usage in the function."""
    body_info = {}
    source = ast.dump(node)

    # Look for request.json, request.get_json(), request.form
    if "request.json" in ast.dump(node) or "get_json" in ast.dump(node):
        body_info["type"] = "json"
    if "request.form" in ast.dump(node):
        body_info["type"] = "form"

    # For FastAPI, look for Pydantic model params
    for arg in node.args.args:
        if arg.annotation and isinstance(arg.annotation, ast.Name):
            if arg.annotation.id not in ("str", "int", "float", "bool", "list", "dict",
                                          "Request", "Response", "BackgroundTasks"):
                body_info["model"] = arg.annotation.id
                body_info["type"] = "json"

    return body_info if body_info else None


def _find_app_variable(tree: ast.Module) -> list[str]:
    """Find Flask/FastAPI app variable names."""
    app_vars = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id in ("Flask", "FastAPI"):
                            app_vars.append(target.id)
                    elif isinstance(node.value.func, ast.Attribute):
                        if node.value.func.attr in ("Flask", "FastAPI"):
                            app_vars.append(target.id)
    return app_vars if app_vars else ["app"]


def _find_blueprint_variables(tree: ast.Module) -> dict:
    """Find Flask Blueprint variables and their URL prefixes."""
    blueprints = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                    func = node.value.func
                    func_name = ""
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    if func_name == "Blueprint":
                        prefix = ""
                        for kw in node.value.keywords:
                            if kw.arg == "url_prefix" and isinstance(kw.value, ast.Constant):
                                prefix = kw.value.value
                        blueprints[target.id] = prefix
    return blueprints


def _find_router_variables(tree: ast.Module) -> dict:
    """Find FastAPI APIRouter variables and their prefixes."""
    routers = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                    func = node.value.func
                    func_name = ""
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    if func_name == "APIRouter":
                        prefix = ""
                        for kw in node.value.keywords:
                            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                prefix = kw.value.value
                        routers[target.id] = prefix
    return routers


def parse_python_code(code: str, framework: str = "auto") -> dict:
    """
    Parse Python API code and extract endpoint information using AST.
    
    Returns a dict with:
    - endpoints: list of endpoint info dicts
    - framework: detected framework
    - language: "python"
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "endpoints": [],
            "framework_detected": "unknown",
            "language": "python",
            "total_endpoints": 0,
            "error": f"Syntax error: {str(e)}"
        }

    if framework == "auto":
        framework = detect_framework(code)

    app_vars = _find_app_variable(tree)
    blueprints = _find_blueprint_variables(tree)
    routers = _find_router_variables(tree)

    all_route_vars = set(app_vars) | set(blueprints.keys()) | set(routers.keys())
    endpoints = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) and not isinstance(node, ast.AsyncFunctionDef):
            continue

        for decorator in node.decorator_list:
            route_info = _extract_route_from_decorator(decorator, all_route_vars, framework)
            if route_info:
                path = route_info["path"]
                methods = route_info["methods"]
                var_name = route_info.get("var_name", "app")

                # Apply blueprint/router prefix
                prefix = blueprints.get(var_name, "") or routers.get(var_name, "")
                if prefix:
                    path = prefix.rstrip("/") + "/" + path.lstrip("/")

                for method in methods:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "function_name": node.name,
                        "parameters": _extract_parameters(node, framework),
                        "docstring": _extract_docstring(node),
                        "request_body": _extract_request_body(node),
                        "line_number": node.lineno,
                        "decorators": [ast.dump(d) for d in node.decorator_list],
                    }
                    endpoints.append(endpoint)

    return {
        "endpoints": endpoints,
        "framework_detected": framework,
        "language": "python",
        "total_endpoints": len(endpoints),
    }


def _extract_route_from_decorator(decorator, route_vars: set, framework: str) -> Optional[dict]:
    """Extract route path and methods from a decorator node."""

    # Pattern 1: @app.route("/path", methods=["GET", "POST"])
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        obj = decorator.func
        var_name = ""
        if isinstance(obj.value, ast.Name):
            var_name = obj.value.id
        attr = obj.attr

        if var_name not in route_vars:
            return None

        # Flask: @app.route(...)
        if attr == "route":
            path = "/"
            methods = ["GET"]
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                path = decorator.args[0].value
            for kw in decorator.keywords:
                if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    methods = []
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Constant):
                            methods.append(elt.value)
            return {"path": path, "methods": methods, "var_name": var_name}

        # FastAPI/Flask: @app.get("/path"), @app.post("/path"), etc.
        if attr.lower() in FLASK_METHODS:
            path = "/"
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                path = decorator.args[0].value
            return {"path": path, "methods": [attr.upper()], "var_name": var_name}

    # Pattern 2: @app.route (no call, rare)
    if isinstance(decorator, ast.Attribute):
        if isinstance(decorator.value, ast.Name) and decorator.value.id in route_vars:
            if decorator.attr.lower() in FLASK_METHODS:
                return {"path": "/", "methods": [decorator.attr.upper()], "var_name": decorator.value.id}

    return None
