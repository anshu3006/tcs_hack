"""
Doc Drift Detector — Compares existing documentation against actual code
to compute a Doc Drift Score™ (0-100).

This is our NOVEL contribution — no existing tool does this.
"""

import re
import json
import os
from typing import Optional
from difflib import SequenceMatcher

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


def _extract_documented_endpoints(docs: str) -> list[dict]:
    """Extract endpoints mentioned in existing documentation."""
    documented = []

    # Pattern 1: `GET /path` or `POST /path` etc.
    endpoint_pattern = re.compile(
        r'`?(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)`?\s+`?(/[^\s`\)]+)`?',
        re.IGNORECASE
    )

    for match in endpoint_pattern.finditer(docs):
        method = match.group(1).upper()
        path = match.group(2).rstrip(",.:;")
        documented.append({
            "method": method,
            "path": path,
            "raw_text": docs[max(0, match.start() - 100):match.end() + 200]
        })

    # Pattern 2: Markdown headers like ### GET /users
    header_pattern = re.compile(
        r'^#{1,4}\s+`?(GET|POST|PUT|DELETE|PATCH)`?\s+`?(/[^\s`]+)`?',
        re.IGNORECASE | re.MULTILINE
    )

    for match in header_pattern.finditer(docs):
        method = match.group(1).upper()
        path = match.group(2).rstrip(",.:;")
        # Check if we already have this one
        existing = any(d["method"] == method and d["path"] == path for d in documented)
        if not existing:
            documented.append({
                "method": method,
                "path": path,
                "raw_text": docs[match.start():match.start() + 300]
            })

    return documented


def _path_similarity(path1: str, path2: str) -> float:
    """Compare two URL paths, accounting for parameter placeholders."""
    # Normalize parameter placeholders
    norm1 = re.sub(r'<[^>]+>|:\w+|\{[^}]+\}', '{param}', path1)
    norm2 = re.sub(r'<[^>]+>|:\w+|\{[^}]+\}', '{param}', path2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def _find_param_changes(code_params: list[dict], doc_text: str) -> list[str]:
    """Find parameters that exist in code but are missing from docs."""
    changes = []
    for param in code_params:
        name = param.get("name", "")
        if name and name not in doc_text:
            changes.append(f"Parameter `{name}` exists in code but not documented")
    return changes


def compute_drift_score(
    code_endpoints: list[dict],
    existing_docs: str,
) -> dict:
    """
    Compute the Doc Drift Score™.
    
    Score meaning:
    0   = Docs perfectly match code
    100 = Docs completely out of sync
    
    Factors:
    - Missing endpoints (endpoints in code but not in docs)
    - Extra endpoints (endpoints in docs but not in code)  
    - Parameter mismatches
    - Outdated descriptions
    """
    
    doc_endpoints = _extract_documented_endpoints(existing_docs)
    
    total_code_eps = len(code_endpoints)
    total_doc_eps = len(doc_endpoints)
    
    if total_code_eps == 0:
        return {
            "drift_score": 0,
            "total_endpoints_in_code": 0,
            "documented_endpoints": total_doc_eps,
            "missing_endpoints": [],
            "outdated_endpoints": [],
            "extra_in_docs": [],
            "summary": "No endpoints found in code."
        }
    
    # Find missing endpoints (in code but not in docs)
    missing_endpoints = []
    matched_endpoints = []
    outdated_endpoints = []
    
    for code_ep in code_endpoints:
        code_method = code_ep.get("method", "GET").upper()
        code_path = code_ep.get("path", "/")
        
        best_match = None
        best_score = 0
        
        for doc_ep in doc_endpoints:
            doc_method = doc_ep.get("method", "GET").upper()
            doc_path = doc_ep.get("path", "/")
            
            if code_method == doc_method:
                sim = _path_similarity(code_path, doc_path)
                if sim > best_score:
                    best_score = sim
                    best_match = doc_ep
        
        if best_match and best_score > 0.8:
            matched_endpoints.append({
                "code": code_ep,
                "doc": best_match,
                "similarity": best_score
            })
            
            # Check for parameter mismatches
            param_changes = _find_param_changes(
                code_ep.get("parameters", []),
                best_match.get("raw_text", "")
            )
            if param_changes:
                outdated_endpoints.append({
                    "method": code_method,
                    "path": code_path,
                    "issues": param_changes,
                    "severity": "medium"
                })
        else:
            missing_endpoints.append(f"{code_method} {code_path}")
    
    # Find extra endpoints (in docs but not in code)
    extra_in_docs = []
    for doc_ep in doc_endpoints:
        doc_method = doc_ep.get("method", "GET").upper()
        doc_path = doc_ep.get("path", "/")
        
        found = False
        for code_ep in code_endpoints:
            if code_ep.get("method", "").upper() == doc_method:
                if _path_similarity(code_ep.get("path", ""), doc_path) > 0.8:
                    found = True
                    break
        
        if not found:
            extra_in_docs.append(f"{doc_method} {doc_path}")
    
    # Calculate drift score
    missing_weight = 40  # Missing endpoints are the biggest issue
    outdated_weight = 30  # Parameter mismatches
    extra_weight = 15     # Extra docs (less critical but still drift)
    coverage_weight = 15  # Overall coverage ratio
    
    missing_penalty = (len(missing_endpoints) / max(total_code_eps, 1)) * missing_weight
    outdated_penalty = (len(outdated_endpoints) / max(total_code_eps, 1)) * outdated_weight
    extra_penalty = (len(extra_in_docs) / max(total_doc_eps, 1)) * extra_weight if total_doc_eps > 0 else 0
    
    coverage_ratio = len(matched_endpoints) / max(total_code_eps, 1)
    coverage_penalty = (1 - coverage_ratio) * coverage_weight
    
    drift_score = min(100, missing_penalty + outdated_penalty + extra_penalty + coverage_penalty)
    drift_score = round(drift_score, 1)
    
    # Generate summary
    if drift_score < 20:
        quality = "🟢 Excellent"
        summary = "Your documentation is well-maintained and closely matches your code."
    elif drift_score < 40:
        quality = "🟡 Good"
        summary = "Documentation is mostly up-to-date with minor gaps."
    elif drift_score < 60:
        quality = "🟠 Needs Attention"
        summary = "Significant documentation drift detected. Several endpoints are undocumented or outdated."
    elif drift_score < 80:
        quality = "🔴 Poor"
        summary = "Documentation is substantially out of sync with your codebase."
    else:
        quality = "⛔ Critical"
        summary = "Documentation is severely outdated and may cause integration issues."
    
    return {
        "drift_score": drift_score,
        "quality": quality,
        "total_endpoints_in_code": total_code_eps,
        "documented_endpoints": len(matched_endpoints),
        "missing_endpoints": missing_endpoints,
        "outdated_endpoints": outdated_endpoints,
        "extra_in_docs": extra_in_docs,
        "summary": summary,
        "breakdown": {
            "missing_penalty": round(missing_penalty, 1),
            "outdated_penalty": round(outdated_penalty, 1),
            "extra_penalty": round(extra_penalty, 1),
            "coverage_penalty": round(coverage_penalty, 1),
        }
    }


def ai_drift_analysis(drift_result: dict, code: str, docs: str) -> str:
    """Use Gemini to provide intelligent drift analysis and recommendations."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or not HAS_GEMINI:
        return _fallback_analysis(drift_result)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        prompt = f"""Analyze this API documentation drift report and provide actionable recommendations:

Drift Score: {drift_result['drift_score']}/100
Missing Endpoints: {json.dumps(drift_result['missing_endpoints'])}
Outdated Endpoints: {json.dumps(drift_result['outdated_endpoints'])}
Extra in Docs: {json.dumps(drift_result.get('extra_in_docs', []))}

Provide:
1. A brief summary of the drift
2. Priority-ordered list of what to fix first
3. Specific recommendations for each missing/outdated endpoint
4. Estimate of effort to fix

Keep it concise and actionable."""

        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return _fallback_analysis(drift_result)


def _fallback_analysis(drift_result: dict) -> str:
    """Generate analysis without AI."""
    lines = [f"## Documentation Drift Analysis\n"]
    lines.append(f"**Drift Score**: {drift_result['drift_score']}/100\n")
    
    if drift_result['missing_endpoints']:
        lines.append("### Missing Documentation\n")
        lines.append("These endpoints exist in your code but have no documentation:\n")
        for ep in drift_result['missing_endpoints']:
            lines.append(f"- ❌ `{ep}`")
        lines.append("")
    
    if drift_result['outdated_endpoints']:
        lines.append("### Outdated Documentation\n")
        for ep in drift_result['outdated_endpoints']:
            lines.append(f"- ⚠️ `{ep['method']} {ep['path']}`")
            for issue in ep.get('issues', []):
                lines.append(f"  - {issue}")
        lines.append("")
    
    if drift_result.get('extra_in_docs'):
        lines.append("### Ghost Endpoints (in docs but not in code)\n")
        for ep in drift_result['extra_in_docs']:
            lines.append(f"- 👻 `{ep}` — may have been removed from code")
        lines.append("")
    
    return "\n".join(lines)
