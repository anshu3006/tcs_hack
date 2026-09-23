"""
Sandbox Executor — Generates a mock API server from parsed endpoints
and handles sandbox execution requests.
"""

import json
import re
from typing import Optional


def generate_mock_responses(endpoints: list[dict]) -> dict:
    """
    Generate realistic mock responses for each endpoint.
    Used by the frontend sandbox to simulate API calls.
    """
    mocks = {}
    
    for ep in endpoints:
        method = ep.get("method", "GET").upper()
        path = ep.get("path", "/")
        func_name = ep.get("function_name", "handler")
        params = ep.get("parameters", [])
        body_fields = ep.get("body_fields", [])
        
        # Generate a key for this endpoint
        key = f"{method} {path}"
        
        # Generate mock response based on endpoint characteristics
        mock = _generate_smart_mock(method, path, func_name, params, body_fields)
        
        mocks[key] = {
            "status": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Mock": "true",
                "X-Powered-By": "DocuLive Sandbox"
            },
            "body": mock,
            "latency_ms": _estimate_latency(method, path)
        }
    
    return mocks


def _generate_smart_mock(method: str, path: str, func_name: str, 
                         params: list, body_fields: list) -> dict:
    """Generate contextually appropriate mock data based on endpoint semantics."""
    
    # Detect the resource from the path
    path_parts = [p for p in path.split("/") if p and not p.startswith("{") and not p.startswith(":") and not p.startswith("<")]
    resource = path_parts[-1] if path_parts else "item"
    resource_singular = resource.rstrip("s") if resource.endswith("s") else resource
    
    # Check if this is a single resource or collection
    has_id_param = bool(re.search(r'[{<:](\w*id\w*)[}>]', path, re.IGNORECASE))
    
    if method == "GET" and not has_id_param:
        # List endpoint
        return {
            "data": [
                _generate_resource_mock(resource_singular, i) for i in range(1, 4)
            ],
            "total": 42,
            "page": 1,
            "per_page": 20
        }
    elif method == "GET" and has_id_param:
        # Single resource
        return {
            "data": _generate_resource_mock(resource_singular, 1)
        }
    elif method == "POST":
        return {
            "message": f"{resource_singular.title()} created successfully",
            "data": _generate_resource_mock(resource_singular, 99),
            "id": 99
        }
    elif method in ("PUT", "PATCH"):
        return {
            "message": f"{resource_singular.title()} updated successfully",
            "data": _generate_resource_mock(resource_singular, 1)
        }
    elif method == "DELETE":
        return {
            "message": f"{resource_singular.title()} deleted successfully",
            "deleted": True
        }
    else:
        return {"status": "ok"}


def _generate_resource_mock(resource: str, id_val: int) -> dict:
    """Generate a mock resource object based on the resource name."""
    base = {
        "id": id_val,
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-06-20T14:22:00Z",
    }
    
    resource_lower = resource.lower()
    
    if resource_lower in ("user", "account", "profile", "member"):
        base.update({
            "name": f"User {id_val}",
            "email": f"user{id_val}@example.com",
            "role": "member",
            "active": True,
        })
    elif resource_lower in ("product", "item", "good"):
        base.update({
            "name": f"Product {id_val}",
            "price": round(19.99 * id_val, 2),
            "description": f"A high-quality {resource_lower}",
            "in_stock": True,
            "category": "general"
        })
    elif resource_lower in ("order", "purchase", "transaction"):
        base.update({
            "user_id": id_val,
            "total": round(49.99 * id_val, 2),
            "status": "completed",
            "items_count": id_val + 1,
        })
    elif resource_lower in ("post", "article", "blog"):
        base.update({
            "title": f"Sample {resource_lower.title()} {id_val}",
            "content": f"This is a sample {resource_lower} content...",
            "author": f"Author {id_val}",
            "published": True,
        })
    elif resource_lower in ("comment", "review"):
        base.update({
            "text": f"This is a sample {resource_lower}",
            "rating": min(5, id_val),
            "user_id": id_val,
        })
    else:
        base.update({
            "name": f"{resource.title()} {id_val}",
            "description": f"A {resource_lower} resource",
            "status": "active"
        })
    
    return base


def _estimate_latency(method: str, path: str) -> int:
    """Estimate realistic latency for the mock."""
    if method == "GET":
        return 50 if "id" not in path.lower() else 30
    elif method == "POST":
        return 120
    elif method in ("PUT", "PATCH"):
        return 80
    elif method == "DELETE":
        return 60
    return 50


def execute_sandbox_request(
    mocks: dict,
    endpoint: str,
    method: str = "GET",
    body: Optional[str] = None,
    headers: Optional[dict] = None,
    query_params: Optional[dict] = None,
) -> dict:
    """
    Execute a sandbox request against the mock server.
    Returns a simulated response.
    """
    key = f"{method.upper()} {endpoint}"
    
    # Try exact match first
    if key in mocks:
        mock = mocks[key]
        response = dict(mock)
        
        # If body was provided, reflect it in the response
        if body and method.upper() in ("POST", "PUT", "PATCH"):
            try:
                body_data = json.loads(body)
                if isinstance(response["body"], dict) and "data" in response["body"]:
                    response["body"]["data"].update(body_data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {
            "status_code": response["status"],
            "headers": response["headers"],
            "body": response["body"],
            "latency_ms": response["latency_ms"],
            "sandbox": True
        }
    
    # Try pattern matching (for parameterized routes)
    for mock_key, mock in mocks.items():
        mock_method, mock_path = mock_key.split(" ", 1)
        if mock_method != method.upper():
            continue
        
        # Convert path params to regex
        pattern = re.sub(r'[{<:](\w+)[}>]', r'[^/]+', mock_path)
        if re.match(f"^{pattern}$", endpoint):
            response = dict(mock)
            return {
                "status_code": response["status"],
                "headers": response["headers"],
                "body": response["body"],
                "latency_ms": response["latency_ms"],
                "sandbox": True
            }
    
    # Endpoint not found
    return {
        "status_code": 404,
        "headers": {"Content-Type": "application/json"},
        "body": {"error": "Endpoint not found", "message": f"No mock defined for {key}"},
        "latency_ms": 5,
        "sandbox": True
    }
