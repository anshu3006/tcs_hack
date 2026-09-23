"""
Headless pipeline runner.

Usage:
    python cli.py path/to/source_file [--out output.json]
"""
import argparse
import json
import sys
from pathlib import Path

from orchestrator import run


def main():
    parser = argparse.ArgumentParser(description="Run the API doc generation pipeline headlessly.")
    parser.add_argument("source_file", help="Path to a code file or OpenAPI spec")
    parser.add_argument("--out", default=None, help="Where to write the resulting JSON (default: stdout)")
    args = parser.parse_args()

    path = Path(args.source_file)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    source_text = path.read_text(encoding="utf-8", errors="ignore")
    result = run(source_text, source_label=path.name)

    output = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).write_text(output)
        print(f"Wrote {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
