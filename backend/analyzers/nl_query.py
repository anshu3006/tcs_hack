"""
Natural Language Query Handler — "Ask Your API" feature.
Delegates to the lightweight RAG engine for semantic search.
"""

from analyzers.rag_engine import rag_engine

def ask_api(question: str, endpoints: list[dict], code: str = "", language: str = "python") -> dict:
    """
    Answer a natural language question about the API using RAG.
    Returns the relevant endpoint(s), a pre-filled example request, and retrieved context.
    """
    
    # Needs to be indexed first? The RAG engine has an `is_indexed` flag.
    # If not indexed for this code, index it now.
    # To keep it simple (for a hackathon demo), we'll just re-index each time if the code isn't empty,
    # or rely on a smart check. Re-indexing every time is fast enough for small hackathon files.
    
    if code and (not rag_engine.is_indexed or len(rag_engine.chunks) == 0):
        rag_engine.index_code(code, language, endpoints)
        
    return rag_engine.query(question, top_k=3)

