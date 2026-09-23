"""
Standalone CLI for Person 2's Doc Writer module.

Runs against a Person-1-shaped JSON file directly, so you can build/demo this
module before the full 3-person pipeline is wired together. Person 3's
orchestrator can shell out to this same entry point, or import generate_all /
score_all / summarize_changes directly.

Examples:
    # with real keys (see .env.example)
    python -m doc_writer.cli --input fixtures/sample_extracted.json --output out/

    # no API keys needed - deterministic placeholder output, good for testing plumbing
    python -m doc_writer.cli --input fixtures/sample_extracted.json --output out/ --provider mock

    # diff against a previous run
    python -m doc_writer.cli --input new_extracted.json --output out2/ --diff-against out/enriched.json
"""
import argparse
import json
import os
from pathlib import Path

from .differ import summarize_changes
from .evaluator import score_all
from .generator import generate_all
from .output_writer import write_eval_report, write_json, write_markdown


def main():
    ap = argparse.ArgumentParser(description="Generate API docs from an extractor JSON schema.")
    ap.add_argument("--input", required=True, help="Path to Person 1's extractor JSON")
    ap.add_argument("--output", required=True, help="Output directory")
    ap.add_argument(
        "--provider",
        default=os.getenv("DOC_WRITER_PROVIDER", "gemini"),
        choices=["gemini", "openrouter", "mock"],
    )
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--no-eval", action="store_true", help="Skip the self-eval scoring pass")
    ap.add_argument("--diff-against", help="Path to a previous run's enriched.json to diff against")
    args = ap.parse_args()

    schema = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    n = len(schema.get("endpoints", []))
    print(f"[doc_writer] generating docs for {n} endpoint(s) via '{args.provider}'...")
    docs = generate_all(schema, provider=args.provider, use_cache=not args.no_cache)
    write_json(docs, out_dir / "enriched.json")
    write_markdown(docs, out_dir / "docs.md", api_name=schema.get("api_name", "API"))
    print(f"[doc_writer] wrote {out_dir / 'enriched.json'} and {out_dir / 'docs.md'}")

    if not args.no_eval:
        print("[doc_writer] running self-eval pass...")
        eval_result = score_all(schema.get("endpoints", []), docs, provider=args.provider)
        write_json(eval_result, out_dir / "eval_raw.json")
        write_eval_report(eval_result, out_dir / "eval_report.md")
        print(
            f"[doc_writer] overall avg score: {eval_result['overall_avg']}/5 "
            f"(target met: {eval_result['meets_80pct_target']})"
        )

    if args.diff_against:
        old_docs = json.loads(Path(args.diff_against).read_text(encoding="utf-8"))
        diff = summarize_changes(old_docs, docs, provider=args.provider)
        write_json(diff, out_dir / "diff.json")
        print(
            f"[doc_writer] diff: +{len(diff['added'])} added, "
            f"-{len(diff['removed'])} removed, ~{len(diff['changed'])} changed"
        )


if __name__ == "__main__":
    main()
