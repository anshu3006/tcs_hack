"""
Streamlit UI for the API Doc Generator.

Run: streamlit run app.py
"""
import json
import streamlit as st
from orchestrator import run

st.set_page_config(page_title="API Doc Generator", layout="wide")

METHOD_COLORS = {
    "GET": "#2f9e44", "POST": "#1971c2", "PUT": "#e8590c",
    "PATCH": "#9c36b5", "DELETE": "#e03131",
}

def method_badge(method: str) -> str:
    color = METHOD_COLORS.get(method.upper(), "#495057")
    return (f'<span style="background:{color};color:white;padding:2px 8px;'
            f'border-radius:4px;font-size:0.75em;font-weight:600;">{method.upper()}</span>')


if "result" not in st.session_state:
    st.session_state.result = None

st.title("API Doc Generator")
st.caption("Paste code, an OpenAPI spec, or upload a file. Pipeline: Extractor → Writer → this UI.")

with st.sidebar:
    st.header("Input")
    mode = st.radio("Source", ["Paste code / spec", "Upload file"], label_visibility="collapsed")
    source_text = ""
    source_label = "pasted-input"
    if mode == "Paste code / spec":
        source_text = st.text_area("Paste your route code or OpenAPI spec", height=220)
    else:
        uploaded = st.file_uploader("Upload file", type=["py", "json", "yaml", "yml"])
        if uploaded:
            source_text = uploaded.read().decode("utf-8", errors="ignore")
            source_label = uploaded.name

    if st.button("Generate documentation", type="primary", use_container_width=True):
        if not source_text.strip():
            st.warning("Paste something or upload a file first.")
        else:
            with st.spinner("Running pipeline..."):
                st.session_state.result = run(source_text, source_label=source_label)

    result = st.session_state.result
    if result:
        st.divider()
        meta = result["meta"]
        if not meta["extractor_is_real"] or not meta["writer_is_real"]:
            st.info("Running with mock extractor/writer (real modules not found in repo root).")
        if meta["avg_eval_score"] is not None:
            st.metric("Avg doc quality score", f"{meta['avg_eval_score']} / 5")
        if meta["diff_summary"]:
            with st.expander("What changed since last run"):
                st.write(meta["diff_summary"])

        st.divider()
        st.subheader("Endpoints")
        search = st.text_input("Search", placeholder="filter by path or method")
        endpoints = result["endpoints"]
        if search:
            s = search.lower()
            endpoints = [e for e in endpoints if s in e["path"].lower() or s in e["method"].lower()]

        labels = [f"{e['method']}  {e['path']}" for e in endpoints]
        selected_idx = st.radio("", range(len(endpoints)),
                                 format_func=lambda i: labels[i],
                                 label_visibility="collapsed") if endpoints else None

# ---- Main panel ----
result = st.session_state.result
if not result:
    st.info("Generate documentation from the sidebar to see results here.")
else:
    endpoints = result["endpoints"]
    if search:
        s = search.lower()
        endpoints = [e for e in endpoints if s in e["path"].lower() or s in e["method"].lower()]

    if not endpoints:
        st.warning("No endpoints match your search.")
    else:
        ep = endpoints[selected_idx if selected_idx is not None else 0]

        st.markdown(f"{method_badge(ep['method'])}  &nbsp; `{ep['path']}`", unsafe_allow_html=True)
        score = ep.get("eval_score", {})
        if score:
            st.caption(f"Clarity {score.get('clarity')}/5 · Completeness {score.get('completeness')}/5 "
                       f"· Avg {score.get('avg')}/5")

        st.markdown("### Description")
        st.write(ep.get("description", "—"))

        params = ep.get("parameters", [])
        if params:
            st.markdown("### Parameters")
            st.table([
                {"name": p["name"], "in": p["in"], "type": p["type"], "required": p["required"],
                 "explanation": ep.get("parameter_explanations", {}).get(p["name"], "")}
                for p in params
            ])

        with st.expander("Request / response example"):
            st.markdown("**Request**")
            st.json(ep.get("examples", {}).get("request", {}))
            st.markdown("**Response**")
            st.json(ep.get("examples", {}).get("response", {}))

        edge_cases = ep.get("edge_cases", [])
        if edge_cases:
            st.markdown("### Edge cases")
            for note in edge_cases:
                st.markdown(f"- {note}")

        st.divider()
        st.download_button(
            "Export this run as JSON",
            data=json.dumps(result, indent=2),
            file_name="api_docs.json",
            mime="application/json",
        )
