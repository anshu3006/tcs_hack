"""
Writes generator/evaluator output as enriched JSON + human-readable Markdown.
Person 3's UI reads enriched.json directly; docs.md and eval_report.md are
for quick human review / the demo video / the repo README.
"""
import json
from pathlib import Path
from typing import Dict, List


def write_json(data, path) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(docs: List[Dict], path, api_name: str = "API") -> None:
    lines = [f"# {api_name} - Generated Documentation", ""]

    for d in docs:
        eid = d.get("endpoint_id") or "?_?"
        method, _, route = eid.partition("_")
        lines.append(f"## `{method}` `{route or eid}`")

        if d.get("error"):
            lines.append(f"> Generation failed: {d['error']}\n")
            continue

        lines.append(d.get("description") or "_No description generated._")
        lines.append("")

        params = d.get("parameters") or []
        if params:
            lines.append("**Parameters**")
            for p in params:
                lines.append(f"- `{p.get('name')}` - {p.get('explanation')}")
            lines.append("")

        if d.get("request_example"):
            lines.append("**Example request**")
            lines.append(f"```\n{d['request_example']}\n```")

        if d.get("response_example"):
            lines.append("**Example response**")
            lines.append(f"```\n{d['response_example']}\n```")

        edge = d.get("edge_cases") or []
        if edge:
            lines.append("**Edge cases**")
            for e in edge:
                lines.append(f"- {e}")

        lines.append("\n---\n")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def write_eval_report(eval_result: Dict, path) -> None:
    lines = [
        "# Self-Eval Report",
        "",
        f"- Endpoints scored: {eval_result['n_scored']}/{eval_result['n_total']}",
        f"- Average clarity: {eval_result['avg_clarity']}/5",
        f"- Average completeness: {eval_result['avg_completeness']}/5",
        f"- **Overall average: {eval_result['overall_avg']}/5**",
        f"- Meets 80% (4.0/5) target: {'yes' if eval_result['meets_80pct_target'] else 'no'}",
        "",
        "## Per-endpoint scores",
        "",
    ]
    for s in eval_result["per_endpoint"]:
        lines.append(
            f"- `{s.get('endpoint_id')}` - clarity {s.get('clarity')}, "
            f"completeness {s.get('completeness')}: {s.get('rationale')}"
        )
    Path(path).write_text("\n".join(lines), encoding="utf-8")
