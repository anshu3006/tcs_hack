#!/usr/bin/env python3
"""
CLI for the extraction half of the pipeline (Person 1's deliverable).

Usage:
    python cli.py extract <input_file> [--type auto|openapi|flask|fastapi|spring] [--out out.json]
    python cli.py extract-dir <directory> --out-dir <output_dir>   # batch mode over fixtures/eval-data
    python cli.py validate <json_file>                             # check a doc against the shared schema

Person 2 should be able to run:
    python cli.py extract fixtures/openapi/petstore.yaml --out /tmp/petstore.schema.json
and get back JSON that conforms to schema/api_schema.json, with zero knowledge
of what the original source file looked like.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractors import flask_fastapi_parser, openapi_parser, spring_parser  # noqa: E402
from schema.models import validate  # noqa: E402

OPENAPI_EXTS = {".yaml", ".yml", ".json"}


def detect_type(path: Path) -> str:
    if path.suffix == ".java":
        return "spring"
    if path.suffix == ".py":
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "FastAPI(" in text or "APIRouter(" in text:
            return "fastapi"
        if "Flask(" in text or "Blueprint(" in text:
            return "flask"
        return "unknown"
    if path.suffix in (".yaml", ".yml", ".json"):
        return "openapi"
    return "unknown"


def extract_one(path: Path, source_type: str) -> dict:
    if source_type == "auto":
        source_type = detect_type(path)
    if source_type == "openapi":
        doc = openapi_parser.parse(path)
    elif source_type in ("flask", "fastapi"):
        doc = flask_fastapi_parser.parse(path)
    elif source_type == "spring":
        doc = spring_parser.parse(path)
    else:
        raise SystemExit(f"Could not determine source type for {path}. Pass --type explicitly.")
    return doc.to_dict()


def cmd_extract(args):
    path = Path(args.input_file)
    result = extract_one(path, args.type)
    errors = validate(result)
    out_text = json.dumps(result, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(out_text)
        print(f"Wrote {args.out} ({len(result['endpoints'])} endpoints)")
    else:
        print(out_text)
    if errors:
        print(f"\n⚠️  {len(errors)} schema validation issue(s):", file=sys.stderr)
        for e in errors:
            print(f"   - {e}", file=sys.stderr)
    if result["extraction_metadata"]["warnings"]:
        print(f"\nℹ️  {len(result['extraction_metadata']['warnings'])} extraction warning(s):", file=sys.stderr)
        for w in result["extraction_metadata"]["warnings"]:
            print(f"   - {w}", file=sys.stderr)


def cmd_extract_dir(args):
    in_dir = Path(args.directory)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(in_dir.rglob("*")):
        if path.suffix not in (".py", ".java", ".yaml", ".yml", ".json"):
            continue
        source_type = detect_type(path)
        if source_type == "unknown":
            continue
        try:
            result = extract_one(path, "auto")
        except Exception as e:  # noqa: BLE001 - batch mode should not die on one bad file
            print(f"skip {path}: {e}", file=sys.stderr)
            continue
        out_path = out_dir / f"{path.stem}.schema.json"
        out_path.write_text(json.dumps(result, indent=2, default=str))
        print(f"{path} -> {out_path} ({len(result['endpoints'])} endpoints, type={source_type})")
        count += 1
    print(f"\nExtracted {count} file(s) into {out_dir}/")


def cmd_validate(args):
    data = json.loads(Path(args.json_file).read_text())
    errors = validate(data)
    if errors:
        print(f"INVALID — {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Valid ✔")


def main():
    parser = argparse.ArgumentParser(description="AutoDoc extractor CLI (Person 1)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Extract one source file to shared-schema JSON")
    p_extract.add_argument("input_file")
    p_extract.add_argument("--type", choices=["auto", "openapi", "flask", "fastapi", "spring"], default="auto")
    p_extract.add_argument("--out", default=None)
    p_extract.set_defaults(func=cmd_extract)

    p_dir = sub.add_parser("extract-dir", help="Batch-extract every recognizable file in a directory")
    p_dir.add_argument("directory")
    p_dir.add_argument("--out-dir", required=True)
    p_dir.set_defaults(func=cmd_extract_dir)

    p_validate = sub.add_parser("validate", help="Validate a JSON file against the shared schema")
    p_validate.add_argument("json_file")
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
