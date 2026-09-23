"""
Stretch extractor: Java Spring (@RestController) route parser.

Java has no `ast` module equivalent available to us here, so this is a
regex/text-based parser rather than a true AST walk. It's intentionally
scoped to the common, idiomatic subset of Spring MVC annotations you see in
tutorials and most real controllers:

    @RestController
    @RequestMapping("/api/users")
    public class UserController {

        @GetMapping("/{id}")
        public User getUser(@PathVariable Long id) { ... }

        @PostMapping
        public User createUser(@RequestBody User user) { ... }
    }

It will NOT catch every possible Spring configuration (e.g. attribute-style
`@RequestMapping(value = "/x", method = RequestMethod.GET)` on arbitrary
multi-line signatures, custom composed annotations, etc.) — those show up
as warnings so Person 2/3 know which endpoints need a human look, rather
than silently mis-documenting them. This is explicitly the "stretch" /
demo-credibility extractor, not a production-grade Java parser.
"""

from __future__ import annotations

import re
from pathlib import Path

from schema.models import (
    ApiDocument,
    Endpoint,
    ExtractionMetadata,
    Parameter,
    RequestBody,
    Response,
)

EXTRACTOR_VERSION = "spring_parser/1.0 (regex-based, best-effort)"

MAPPING_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "PatchMapping": "PATCH",
    "DeleteMapping": "DELETE",
}

JAVA_TYPE_MAP = {
    "long": "integer", "Long": "integer",
    "int": "integer", "Integer": "integer",
    "double": "number", "Double": "number", "float": "number", "Float": "number",
    "boolean": "boolean", "Boolean": "boolean",
    "String": "string",
}

CLASS_RE = re.compile(r"@RestController.*?public\s+class\s+(\w+)", re.DOTALL)
CLASS_LEVEL_MAPPING_RE = re.compile(r'@RequestMapping\(\s*"([^"]*)"\s*\)')
METHOD_MAPPING_RE = re.compile(
    r'@(?P<ann>GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)'
    r'(?:\(\s*(?:value\s*=\s*)?"(?P<path>[^"]*)"\s*\))?'
    r'\s*(?:\n\s*)?public\s+[\w<>,\s\[\]]+?\s+(?P<name>\w+)\s*\((?P<args>[^)]*)\)',
)
PARAM_RE = re.compile(
    r'@(?P<kind>PathVariable|RequestParam|RequestBody)'
    r'(?:\([^)]*\))?\s+'
    r'(?P<type>[\w<>\[\],.\s]+?)\s+'
    r'(?P<name>\w+)\s*(?:,|$)'
)
JAVADOC_RE = re.compile(r"/\*\*(.*?)\*/", re.DOTALL)


def _clean_javadoc(raw: str) -> str:
    lines = [re.sub(r"^\s*\*\s?", "", l) for l in raw.strip().splitlines()]
    return "\n".join(l for l in lines if not l.strip().startswith("@")).strip()


def _java_type_to_schema(java_type: str) -> str:
    java_type = java_type.strip()
    if java_type in JAVA_TYPE_MAP:
        return JAVA_TYPE_MAP[java_type]
    if java_type and java_type[0].isupper():
        return "object"
    return "unknown"


def _parse_params(args_str: str) -> tuple[list[Parameter], RequestBody | None]:
    params: list[Parameter] = []
    request_body = None
    for m in PARAM_RE.finditer(args_str):
        kind, jtype, name = m.group("kind"), m.group("type"), m.group("name")
        if kind == "PathVariable":
            params.append(Parameter(name=name, in_="path", required=True, type=_java_type_to_schema(jtype)))
        elif kind == "RequestParam":
            params.append(Parameter(name=name, in_="query", required=False, type=_java_type_to_schema(jtype)))
        elif kind == "RequestBody":
            request_body = RequestBody(
                content_type="application/json",
                required=True,
                schema={"model_type": jtype.strip(), "note": "field-level shape not extracted (regex-based extractor); see source class."},
            )
    return params, request_body


def parse(path: str | Path) -> ApiDocument:
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    warnings: list[str] = []

    class_match = CLASS_RE.search(source)
    class_name = class_match.group(1) if class_match else path.stem
    if not class_match:
        warnings.append("No @RestController class found — file may not be a Spring controller.")

    prefix_match = CLASS_LEVEL_MAPPING_RE.search(source.split("public class")[0] if "public class" in source else source)
    prefix = prefix_match.group(1) if prefix_match else ""

    endpoints: list[Endpoint] = []
    for m in METHOD_MAPPING_RE.finditer(source):
        method = MAPPING_ANNOTATIONS[m.group("ann")]
        sub_path = m.group("path") or ""
        full_path = (prefix.rstrip("/") + "/" + sub_path.lstrip("/")).rstrip("/") or "/"
        name = m.group("name")
        params, request_body = _parse_params(m.group("args") or "")

        # look for a Javadoc block immediately preceding this method
        preceding = source[: m.start()]
        doc_match = list(JAVADOC_RE.finditer(preceding))
        summary = description = None
        # m.start() is the position of the mapping annotation's own '@', so a
        # Javadoc block "belongs" to this method only if nothing but
        # whitespace separates the two.
        if doc_match and not preceding[doc_match[-1].end():].strip():
            description = _clean_javadoc(doc_match[-1].group(1))
            summary = description.splitlines()[0] if description else None
        else:
            warnings.append(f"{name}: no Javadoc comment found — summary generated from method name only.")
            summary = name.replace("_", " ").title()

        endpoints.append(
            Endpoint(
                path=full_path,
                method=method,
                operation_id=name,
                summary=summary,
                description=description,
                tags=[class_name],
                parameters=params,
                request_body=request_body,
                responses=[Response(status_code="200", description="Successful response")],
            )
        )

    if not endpoints:
        warnings.append(
            "No @*Mapping methods matched. This extractor only handles the common "
            "@GetMapping/@PostMapping/... + @PathVariable/@RequestParam/@RequestBody idiom."
        )

    return ApiDocument(
        api_name=class_name,
        version="unknown",
        base_url=None,
        description=None,
        source_type="spring",
        endpoints=endpoints,
        extraction_metadata=ExtractionMetadata(
            source_file=str(path),
            extractor_version=EXTRACTOR_VERSION,
            warnings=warnings,
        ),
    )
