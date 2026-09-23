from pydantic import BaseModel
from typing import Optional


class ParseRequest(BaseModel):
    code: str
    language: str = "python"  # "python" | "javascript" | "openapi"
    framework: str = "auto"   # "flask" | "fastapi" | "express" | "auto"


class GenerateDocsRequest(BaseModel):
    code: str
    language: str = "python"
    framework: str = "auto"
    style: str = "stripe"  # "stripe" | "minimal" | "detailed"


class DriftRequest(BaseModel):
    code: str
    existing_docs: str
    language: str = "python"
    framework: str = "auto"


class AskApiRequest(BaseModel):
    question: str
    code: str
    language: str = "python"
    framework: str = "auto"


class SandboxRequest(BaseModel):
    code: str
    endpoint: str
    method: str = "GET"
    body: Optional[str] = None
    headers: Optional[dict] = None
    query_params: Optional[dict] = None


class GitHubFetchRequest(BaseModel):
    repo_url: str
    file_path: Optional[str] = None


class EndpointInfo(BaseModel):
    path: str
    method: str
    function_name: str
    parameters: list = []
    decorators: list = []
    docstring: Optional[str] = None
    request_body: Optional[dict] = None
    response_model: Optional[str] = None
    line_number: int = 0


class ParseResponse(BaseModel):
    endpoints: list[dict]
    framework_detected: str
    language: str
    total_endpoints: int


class DocGenerationResponse(BaseModel):
    markdown: str
    openapi_spec: Optional[dict] = None
    endpoints_documented: int


class DriftResponse(BaseModel):
    drift_score: float  # 0-100
    total_endpoints_in_code: int
    documented_endpoints: int
    missing_endpoints: list[str]
    outdated_endpoints: list[dict]
    summary: str


class AskApiResponse(BaseModel):
    answer: str
    relevant_endpoints: list[dict]
    example_request: Optional[dict] = None
