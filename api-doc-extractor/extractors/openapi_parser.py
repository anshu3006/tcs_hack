"""
OpenAPI 3.x / Swagger 2.0 parser.

This is the reliable baseline extractor: OpenAPI/Swagger files are already
structured, so we mostly reshape them into the shared schema rather than
inferring anything. Supports both JSON and YAML input, and both OpenAPI 3.x
(`openapi: 3.x.x`) and Swagger 2.0 (`swagger: "2.0"`) documents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from schema.models import (
    ApiDocument,
    Endpoint,
    ExtractionMetadata,
    Parameter,
    RequestBody,
    Response,
)

EXTRACTOR_VERSION = "openapi_parser/1.0"
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _load_raw(path: str | Path) -> dict:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    # yaml.safe_load also correctly parses JSON, so default to YAML for
    # .yaml/.yml and for anything ambiguous.
    return yaml.safe_load(text)


def _resolve_ref(ref: str, root: dict) -> dict:
    """Resolve a local '#/components/schemas/Foo' (or Swagger 2 '#/definitions/Foo') ref."""
    if not ref.startswith("#/"):
        return {}
    node: Any = root
    for part in ref.lstrip("#/").split("/"):
        node = node.get(part, {}) if isinstance(node, dict) else {}
    return node if isinstance(node, dict) else {}


def _schema_type(schema: dict, root: dict, warnings: list[str], depth: int = 0) -> tuple[str, dict | None]:
    """Return (type_name, simplified_shape) for a JSON-schema-ish node, following one level of $ref."""
    if not schema:
        return "unknown", None
    if "$ref" in schema:
        if depth > 5:
            warnings.append(f"$ref cycle too deep at {schema['$ref']}")
            return "object", None
        resolved = _resolve_ref(schema["$ref"], root)
        return _schema_type(resolved, root, warnings, depth + 1)
    t = schema.get("type", "object")
    if t == "array":
        item_type, item_shape = _schema_type(schema.get("items", {}), root, warnings, depth + 1)
        return "array", {"items_type": item_type, "items_shape": item_shape}
    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        fields = {}
        for name, prop_schema in props.items():
            ptype, _ = _schema_type(prop_schema, root, warnings, depth + 1)
            fields[name] = {"type": ptype, "required": name in required}
        return "object", {"fields": fields} if fields else None
    return t or "unknown", None


def _extract_parameters(raw_params: list[dict], root: dict, warnings: list[str]) -> list[Parameter]:
    params = []
    for p in raw_params or []:
        if "$ref" in p:
            p = _resolve_ref(p["$ref"], root)
        schema = p.get("schema", {"type": p.get("type", "unknown")})  # Swagger 2 puts type directly on param
        ptype, _ = _schema_type(schema, root, warnings)
        params.append(
            Parameter(
                name=p.get("name", "unknown"),
                in_=p.get("in", "query"),
                required=bool(p.get("required", False)),
                type=ptype,
                default=schema.get("default"),
                description=p.get("description"),
                example=p.get("example"),
            )
        )
    return params


def _extract_request_body(operation: dict, root: dict, warnings: list[str]) -> RequestBody | None:
    # OpenAPI 3.x
    rb = operation.get("requestBody")
    if rb:
        if "$ref" in rb:
            rb = _resolve_ref(rb["$ref"], root)
        content = rb.get("content", {})
        content_type = next(iter(content), "application/json")
        media = content.get(content_type, {})
        schema = media.get("schema", {})
        _, shape = _schema_type(schema, root, warnings)
        return RequestBody(
            content_type=content_type,
            required=bool(rb.get("required", False)),
            schema=shape,
            example=media.get("example"),
        )
    # Swagger 2.0: body param carries the schema
    for p in operation.get("parameters", []):
        if p.get("in") == "body":
            schema = p.get("schema", {})
            _, shape = _schema_type(schema, root, warnings)
            return RequestBody(content_type="application/json", required=bool(p.get("required", False)), schema=shape)
    return None


def _extract_responses(operation: dict, root: dict, warnings: list[str]) -> list[Response]:
    out = []
    for status, resp in (operation.get("responses") or {}).items():
        if "$ref" in resp:
            resp = _resolve_ref(resp["$ref"], root)
        schema_shape = None
        example = None
        content = resp.get("content", {})
        if content:
            content_type = next(iter(content), "application/json")
            media = content.get(content_type, {})
            _, schema_shape = _schema_type(media.get("schema", {}), root, warnings)
            example = media.get("example")
        elif "schema" in resp:  # Swagger 2.0
            _, schema_shape = _schema_type(resp["schema"], root, warnings)
        out.append(
            Response(
                status_code=str(status),
                description=resp.get("description"),
                schema=schema_shape,
                example=example,
            )
        )
    return out


def parse(path: str | Path) -> ApiDocument:
    path = Path(path)
    raw = _load_raw(path)
    warnings: list[str] = []

    is_v3 = "openapi" in raw
    info = raw.get("info", {})

    base_url = None
    if is_v3 and raw.get("servers"):
        base_url = raw["servers"][0].get("url")
    elif not is_v3:
        scheme = (raw.get("schemes") or ["https"])[0]
        host = raw.get("host", "")
        base_path = raw.get("basePath", "")
        base_url = f"{scheme}://{host}{base_path}" if host else None

    endpoints: list[Endpoint] = []
    for route_path, path_item in (raw.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        # parameters common to all methods on this path
        shared_params = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            all_params = _extract_parameters(shared_params + operation.get("parameters", []), raw, warnings)
            endpoints.append(
                Endpoint(
                    path=route_path,
                    method=method.upper(),
                    operation_id=operation.get("operationId"),
                    summary=operation.get("summary"),
                    description=operation.get("description"),
                    tags=operation.get("tags", []),
                    parameters=all_params,
                    request_body=_extract_request_body(operation, raw, warnings),
                    responses=_extract_responses(operation, raw, warnings),
                    deprecated=bool(operation.get("deprecated", False)),
                    source_location=None,  # OpenAPI files don't carry line-level source info
                )
            )

    if not endpoints:
        warnings.append("No endpoints found — check that 'paths' is populated in the spec.")

    return ApiDocument(
        api_name=info.get("title", path.stem),
        version=str(info.get("version", "unknown")),
        base_url=base_url,
        description=info.get("description"),
        source_type="openapi",
        endpoints=endpoints,
        extraction_metadata=ExtractionMetadata(
            source_file=str(path),
            extractor_version=EXTRACTOR_VERSION,
            warnings=warnings,
        ),
    )
