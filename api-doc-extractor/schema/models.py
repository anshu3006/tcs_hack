"""
Shared data model for the AutoDoc project.

Every extractor (openapi_parser, flask_fastapi_parser, spring_parser, ...)
builds these dataclasses and serializes them with `to_dict()`. The resulting
JSON is what gets handed to Person 2 (Doc Writer) — it is the *only* contract
between the two halves of the pipeline, so changes here must stay in sync
with schema/api_schema.json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jsonschema

SCHEMA_PATH = Path(__file__).parent / "api_schema.json"


@dataclass
class Parameter:
    name: str
    in_: str  # "path" | "query" | "header" | "cookie" | "body"  (aliased because `in` is a keyword)
    required: bool
    type: str = "unknown"
    default: Any = None
    description: Optional[str] = None
    example: Any = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "in": self.in_,
            "required": self.required,
            "type": self.type,
            "default": self.default,
            "description": self.description,
            "example": self.example,
        }


@dataclass
class RequestBody:
    content_type: str = "application/json"
    required: bool = False
    schema: Optional[dict] = None
    example: Any = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Response:
    status_code: str
    description: Optional[str] = None
    schema: Optional[dict] = None
    example: Any = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SourceLocation:
    file: str
    line: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Endpoint:
    path: str
    method: str
    parameters: list[Parameter] = field(default_factory=list)
    responses: list[Response] = field(default_factory=list)
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    deprecated: bool = False
    source_location: Optional[SourceLocation] = None

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "method": self.method,
            "operation_id": self.operation_id,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_body": self.request_body.to_dict() if self.request_body else None,
            "responses": [r.to_dict() for r in self.responses],
            "deprecated": self.deprecated,
            "source_location": self.source_location.to_dict() if self.source_location else None,
        }


@dataclass
class ExtractionMetadata:
    source_file: str
    extractor_version: str
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApiDocument:
    api_name: str
    version: str
    source_type: str  # "openapi" | "flask" | "fastapi" | "spring" | "unknown"
    endpoints: list[Endpoint]
    extraction_metadata: ExtractionMetadata
    base_url: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "api_name": self.api_name,
            "version": self.version,
            "base_url": self.base_url,
            "description": self.description,
            "source_type": self.source_type,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "extraction_metadata": self.extraction_metadata.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


def validate(doc: dict) -> list[str]:
    """
    Validate a dict against schema/api_schema.json.
    Returns a list of human-readable error strings (empty list == valid).
    """
    schema = json.loads(SCHEMA_PATH.read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in errors]
