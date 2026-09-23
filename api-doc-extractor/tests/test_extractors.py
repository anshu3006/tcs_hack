import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from extractors import flask_fastapi_parser, openapi_parser, spring_parser  # noqa: E402
from schema.models import validate  # noqa: E402

FIXTURES = ROOT / "fixtures"


# ---------------------------------------------------------------------------
# OpenAPI / Swagger
# ---------------------------------------------------------------------------

def test_openapi_petstore_basic_shape():
    doc = openapi_parser.parse(FIXTURES / "openapi" / "petstore.yaml")
    d = doc.to_dict()
    assert d["source_type"] == "openapi"
    assert d["api_name"] == "Swagger Petstore"
    paths = {e["path"] for e in d["endpoints"]}
    assert "/pets" in paths and "/pets/{petId}" in paths
    assert not validate(d)


def test_openapi_petstore_get_pets_has_query_param():
    doc = openapi_parser.parse(FIXTURES / "openapi" / "petstore.yaml")
    get_pets = next(e for e in doc.to_dict()["endpoints"] if e["path"] == "/pets" and e["method"] == "GET")
    param_names = {p["name"] for p in get_pets["parameters"]}
    assert "limit" in param_names


def test_openapi_petstore_post_pets_has_request_body():
    doc = openapi_parser.parse(FIXTURES / "openapi" / "petstore.yaml")
    post_pets = next(e for e in doc.to_dict()["endpoints"] if e["path"] == "/pets" and e["method"] == "POST")
    assert post_pets["request_body"] is not None
    assert post_pets["request_body"]["required"] is True


def test_swagger2_task_api():
    doc = openapi_parser.parse(FIXTURES / "openapi" / "task-api.swagger2.json")
    d = doc.to_dict()
    assert d["source_type"] == "openapi"
    assert d["base_url"] == "https://tasks.example.com/v1"
    get_task = next(e for e in d["endpoints"] if e["path"] == "/tasks/{taskId}" and e["method"] == "GET")
    assert get_task["parameters"][0]["name"] == "taskId"
    assert get_task["parameters"][0]["in"] == "path"
    assert get_task["parameters"][0]["type"] == "integer"
    assert not validate(d)


# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------

def test_flask_blog_api_endpoint_count():
    doc = flask_fastapi_parser.parse(FIXTURES / "flask" / "blog_api.py")
    d = doc.to_dict()
    assert d["source_type"] == "flask"
    assert len(d["endpoints"]) == 6
    assert not validate(d)


def test_flask_path_param_type_from_converter():
    doc = flask_fastapi_parser.parse(FIXTURES / "flask" / "blog_api.py")
    d = doc.to_dict()
    get_post = next(e for e in d["endpoints"] if e["path"] == "/posts/<int:post_id>" and e["method"] == "GET")
    path_params = [p for p in get_post["parameters"] if p["in"] == "path"]
    assert path_params[0]["name"] == "post_id"
    assert path_params[0]["type"] == "integer"


def test_flask_detects_query_arg_from_request_args():
    doc = flask_fastapi_parser.parse(FIXTURES / "flask" / "blog_api.py")
    d = doc.to_dict()
    list_posts = next(e for e in d["endpoints"] if e["path"] == "/posts" and e["method"] == "GET")
    query_params = {p["name"] for p in list_posts["parameters"] if p["in"] == "query"}
    assert "author" in query_params


def test_flask_warns_on_get_json_without_types():
    doc = flask_fastapi_parser.parse(FIXTURES / "flask" / "blog_api.py")
    warnings = doc.to_dict()["extraction_metadata"]["warnings"]
    assert any("get_json" in w for w in warnings)


# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------

def test_fastapi_items_api_endpoint_count():
    doc = flask_fastapi_parser.parse(FIXTURES / "fastapi" / "items_api.py")
    d = doc.to_dict()
    assert d["source_type"] == "fastapi"
    assert len(d["endpoints"]) == 5
    assert not validate(d)


def test_fastapi_path_param_type_from_annotation():
    doc = flask_fastapi_parser.parse(FIXTURES / "fastapi" / "items_api.py")
    d = doc.to_dict()
    get_item = next(e for e in d["endpoints"] if e["path"] == "/items/{item_id}" and e["method"] == "GET")
    path_params = [p for p in get_item["parameters"] if p["in"] == "path"]
    assert path_params[0]["type"] == "integer"


def test_fastapi_request_body_from_pydantic_model():
    doc = flask_fastapi_parser.parse(FIXTURES / "fastapi" / "items_api.py")
    d = doc.to_dict()
    create_item = next(e for e in d["endpoints"] if e["path"] == "/items" and e["method"] == "POST")
    assert create_item["request_body"] is not None
    fields = create_item["request_body"]["schema"]["fields"]
    assert fields["name"]["type"] == "string"
    assert fields["price"]["type"] == "number"
    assert fields["description"]["required"] is False


def test_fastapi_query_param_with_default():
    doc = flask_fastapi_parser.parse(FIXTURES / "fastapi" / "items_api.py")
    d = doc.to_dict()
    list_items = next(e for e in d["endpoints"] if e["path"] == "/items" and e["method"] == "GET")
    limit_param = next(p for p in list_items["parameters"] if p["name"] == "limit")
    assert limit_param["required"] is False
    assert limit_param["type"] == "integer"
    assert limit_param["default"] == 20


# ---------------------------------------------------------------------------
# Spring (stretch)
# ---------------------------------------------------------------------------

def test_spring_user_controller_endpoint_count():
    doc = spring_parser.parse(FIXTURES / "spring" / "UserController.java")
    d = doc.to_dict()
    assert d["source_type"] == "spring"
    assert len(d["endpoints"]) == 5
    assert not validate(d)


def test_spring_path_prefix_applied():
    doc = spring_parser.parse(FIXTURES / "spring" / "UserController.java")
    d = doc.to_dict()
    paths = {e["path"] for e in d["endpoints"]}
    assert "/api/users" in paths
    assert "/api/users/{id}" in paths


def test_spring_javadoc_becomes_description():
    doc = spring_parser.parse(FIXTURES / "spring" / "UserController.java")
    d = doc.to_dict()
    get_user = next(e for e in d["endpoints"] if e["path"] == "/api/users/{id}" and e["method"] == "GET")
    assert "numeric ID" in get_user["description"]


def test_spring_request_body_flagged_for_followup():
    doc = spring_parser.parse(FIXTURES / "spring" / "UserController.java")
    d = doc.to_dict()
    create_user = next(e for e in d["endpoints"] if e["path"] == "/api/users" and e["method"] == "POST")
    assert create_user["request_body"] is not None
    assert create_user["request_body"]["schema"]["model_type"] == "User"


# ---------------------------------------------------------------------------
# Schema self-validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "parser_module,fixture_path,kwarg",
    [
        (openapi_parser, "openapi/petstore.yaml", None),
        (openapi_parser, "openapi/petstore-expanded.yaml", None),
        (openapi_parser, "openapi/task-api.swagger2.json", None),
        (flask_fastapi_parser, "flask/blog_api.py", None),
        (flask_fastapi_parser, "fastapi/items_api.py", None),
        (spring_parser, "spring/UserController.java", None),
    ],
)
def test_every_fixture_produces_schema_valid_output(parser_module, fixture_path, kwarg):
    doc = parser_module.parse(FIXTURES / fixture_path)
    errors = validate(doc.to_dict())
    assert errors == [], f"{fixture_path}: {errors}"
