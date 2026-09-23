"""
Static-analysis parser for Flask and FastAPI apps, built on Python's `ast`
module — no code is imported or executed, so it's safe to run on arbitrary
untrusted source files.

What it detects:
  - App/router/blueprint instantiation: `app = Flask(__name__)`,
    `app = FastAPI()`, `router = APIRouter()`, `bp = Blueprint(...)`
  - Route decorators: `@app.route("/x", methods=["GET","POST"])` (Flask),
    `@app.get("/x")` / `@router.post("/x")` (FastAPI)
  - Path parameters: Flask's `<int:id>` converters and FastAPI's `{id}`
    placeholders, cross-referenced against the function signature for types
  - FastAPI query params from typed function arguments with defaults
  - FastAPI request bodies / response models via locally-defined
    `class Foo(BaseModel): ...` classes
  - Flask request bodies/query args via a light scan of the function body
    for `request.args.get(...)` / `request.get_json()` calls
  - Docstrings -> summary/description

Anything it can't confidently infer is recorded in `extraction_metadata.warnings`
instead of guessed at, so Person 2/3 can flag low-confidence sections rather
than silently generating wrong docs.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Optional

from schema.models import (
    ApiDocument,
    Endpoint,
    ExtractionMetadata,
    Parameter,
    RequestBody,
    Response,
    SourceLocation,
)

EXTRACTOR_VERSION = "flask_fastapi_parser/1.0"

FASTAPI_METHOD_DECORATORS = {"get", "post", "put", "patch", "delete", "head", "options"}
FLASK_ROUTE_DECORATOR = "route"

TYPE_MAP = {
    "int": "integer",
    "str": "string",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "List": "array",
    "dict": "object",
    "Dict": "object",
}

FLASK_CONVERTER_MAP = {
    "int": "integer",
    "float": "number",
    "string": "string",
    "path": "string",
    "uuid": "string",
    "": "string",  # no converter specified, e.g. <name>
}


def normalize_type(annotation_str: Optional[str]) -> str:
    """Map a Python type-hint string (as text, e.g. 'Optional[int]', 'List[str]') to a schema type name."""
    if not annotation_str:
        return "unknown"
    base = re.split(r"[\[\], ]", annotation_str)[0]
    if base == "Optional":
        inner = re.findall(r"\[([a-zA-Z_][a-zA-Z0-9_.]*)", annotation_str)
        base = inner[0] if inner else annotation_str
    if base in TYPE_MAP:
        return TYPE_MAP[base]
    if base and base[0].isupper():
        return "object"  # assume a class reference (Pydantic model or other custom type)
    return "unknown"


def _unparse(node) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _literal(node):
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


def _docstring_parts(node) -> tuple[Optional[str], Optional[str]]:
    doc = ast.get_docstring(node)
    if not doc:
        return None, None
    lines = [l.strip() for l in doc.strip().splitlines() if l.strip()]
    summary = lines[0] if lines else None
    description = doc.strip()
    return summary, description


class PydanticModelCollector(ast.NodeVisitor):
    """Collects `class Foo(BaseModel): field: type = default` field shapes."""

    def __init__(self):
        self.models: dict[str, dict] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        base_names = {(_unparse(b) or "") for b in node.bases}
        if any("BaseModel" in b for b in base_names):
            fields = {}
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    type_str = _unparse(stmt.annotation)
                    fields[stmt.target.id] = {
                        "type": normalize_type(type_str),
                        "required": stmt.value is None,
                    }
            self.models[node.name] = {"fields": fields}
        self.generic_visit(node)


class AppVarCollector(ast.NodeVisitor):
    """Finds variable names bound to Flask()/FastAPI()/APIRouter()/Blueprint()."""

    def __init__(self):
        self.flask_vars: set[str] = set()
        self.fastapi_vars: set[str] = set()

    def visit_Assign(self, node: ast.Assign):
        if isinstance(node.value, ast.Call):
            callee = _unparse(node.value.func) or ""
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if callee.endswith("Flask") or callee.endswith("Blueprint"):
                    self.flask_vars.add(target.id)
                elif callee.endswith("FastAPI") or callee.endswith("APIRouter"):
                    self.fastapi_vars.add(target.id)
        self.generic_visit(node)


def _parse_flask_path_params(path: str) -> list[Parameter]:
    params = []
    for converter, name in re.findall(r"<(?:([a-zA-Z]+):)?([a-zA-Z_][a-zA-Z0-9_]*)>", path):
        params.append(
            Parameter(
                name=name,
                in_="path",
                required=True,
                type=FLASK_CONVERTER_MAP.get(converter, "string"),
            )
        )
    return params


def _parse_braced_path_params(path: str) -> set[str]:
    return set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", path))


def _scan_flask_body_for_query_args(func_node: ast.FunctionDef, warnings: list[str]) -> list[Parameter]:
    """Best-effort: look for request.args.get('x') / request.args['x'] inside the view function."""
    found: dict[str, Parameter] = {}
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            f = node.func
            if (
                isinstance(f, ast.Attribute)
                and f.attr == "get"
                and isinstance(f.value, ast.Attribute)
                and f.value.attr == "args"
            ):
                if node.args:
                    name = _literal(node.args[0])
                    if isinstance(name, str) and name not in found:
                        found[name] = Parameter(name=name, in_="query", required=False, type="string")
        if isinstance(node, ast.Subscript):
            val = node.value
            if isinstance(val, ast.Attribute) and val.attr == "args":
                name = _literal(node.slice)
                if isinstance(name, str) and name not in found:
                    found[name] = Parameter(name=name, in_="query", required=True, type="string")
    if any(
        isinstance(n, ast.Attribute) and n.attr == "get_json"
        for n in ast.walk(func_node)
    ):
        warnings.append(
            f"{func_node.name}: uses request.get_json() — body shape could not be statically inferred "
            "(no type hints available); document manually or add a Pydantic/marshmallow schema."
        )
    return list(found.values())


def _fastapi_endpoint_params(
    func_node: ast.FunctionDef,
    path_param_names: set[str],
    models: dict[str, dict],
    warnings: list[str],
) -> tuple[list[Parameter], Optional[RequestBody]]:
    params: list[Parameter] = []
    request_body: Optional[RequestBody] = None
    args = func_node.args.args
    defaults = [None] * (len(args) - len(func_node.args.defaults)) + list(func_node.args.defaults)

    for arg, default in zip(args, defaults):
        if arg.arg in ("self", "request"):
            continue
        type_str = _unparse(arg.annotation)
        base_type = (type_str or "").split("[")[0].replace("Optional", "").strip()

        if arg.arg in path_param_names:
            params.append(Parameter(name=arg.arg, in_="path", required=True, type=normalize_type(type_str)))
            continue

        if base_type in models:
            fields = models[base_type]["fields"]
            request_body = RequestBody(content_type="application/json", required=True, schema={"fields": fields})
            continue

        has_default = default is not None
        default_val = _literal(default) if has_default else None
        params.append(
            Parameter(
                name=arg.arg,
                in_="query",
                required=not has_default,
                type=normalize_type(type_str),
                default=default_val,
            )
        )
        if not type_str:
            warnings.append(f"{func_node.name}: parameter '{arg.arg}' has no type hint — typed as 'unknown'.")

    return params, request_body


def _fastapi_response_model(decorator: ast.Call, models: dict[str, dict]) -> tuple[Optional[dict], str]:
    status_code = "200"
    schema = None
    for kw in decorator.keywords or []:
        if kw.arg == "response_model":
            name = _unparse(kw.value)
            if name in models:
                schema = {"fields": models[name]["fields"]}
        if kw.arg == "status_code":
            val = _literal(kw.value)
            if val is not None:
                status_code = str(val)
    return schema, status_code


def parse(path: str | Path) -> ApiDocument:
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    warnings: list[str] = []

    app_vars = AppVarCollector()
    app_vars.visit(tree)

    model_collector = PydanticModelCollector()
    model_collector.visit(tree)

    endpoints: list[Endpoint] = []
    is_fastapi = bool(app_vars.fastapi_vars)
    is_flask = bool(app_vars.flask_vars)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or not isinstance(dec.func, ast.Attribute):
                continue
            owner = dec.func.value
            owner_name = owner.id if isinstance(owner, ast.Name) else None
            attr = dec.func.attr

            route_path = None
            methods = []
            if owner_name in app_vars.flask_vars and attr == FLASK_ROUTE_DECORATOR:
                if dec.args:
                    route_path = _literal(dec.args[0])
                for kw in dec.keywords or []:
                    if kw.arg == "methods":
                        methods = _literal(kw.value) or ["GET"]
                methods = methods or ["GET"]
                source_type = "flask"
            elif owner_name in app_vars.fastapi_vars and attr in FASTAPI_METHOD_DECORATORS:
                if dec.args:
                    route_path = _literal(dec.args[0])
                methods = [attr.upper()]
                source_type = "fastapi"
            else:
                continue

            if route_path is None:
                warnings.append(f"{node.name}: could not statically resolve route path (non-literal argument).")
                continue

            summary, description = _docstring_parts(node)

            if source_type == "flask":
                path_params = _parse_flask_path_params(route_path)
                query_params = _scan_flask_body_for_query_args(node, warnings)
                all_params = path_params + query_params
                request_body = None
                responses = [Response(status_code="200", description="Successful response")]
                if not node.decorator_list or not ast.get_docstring(node):
                    warnings.append(f"{node.name}: no docstring — description generated from route only.")
            else:  # fastapi
                path_param_names = _parse_braced_path_params(route_path)
                all_params, request_body = _fastapi_endpoint_params(
                    node, path_param_names, model_collector.models, warnings
                )
                resp_schema, status_code = _fastapi_response_model(dec, model_collector.models)
                responses = [Response(status_code=status_code, description="Successful response", schema=resp_schema)]

            for method in methods:
                endpoints.append(
                    Endpoint(
                        path=route_path,
                        method=method.upper(),
                        operation_id=node.name,
                        summary=summary or node.name.replace("_", " ").title(),
                        description=description,
                        parameters=all_params,
                        request_body=request_body,
                        responses=responses,
                        source_location=SourceLocation(file=str(path), line=node.lineno),
                    )
                )

    if is_fastapi and is_flask:
        warnings.append("Both Flask and FastAPI app objects detected in one file — verify results manually.")
    if not endpoints:
        warnings.append("No routes detected. Confirm the file defines Flask/FastAPI routes with literal path strings.")

    resolved_source_type = "fastapi" if is_fastapi else ("flask" if is_flask else "unknown")

    return ApiDocument(
        api_name=path.stem,
        version="unknown",
        base_url=None,
        description=ast.get_docstring(tree),
        source_type=resolved_source_type,
        endpoints=endpoints,
        extraction_metadata=ExtractionMetadata(
            source_file=str(path),
            extractor_version=EXTRACTOR_VERSION,
            warnings=warnings,
        ),
    )
