"""
Lightweight RAG Engine — Retrieval Augmented Generation for API documentation.

Uses Gemini Embeddings for vectorization and cosine similarity for retrieval.
No external vector DB needed — runs entirely in-memory.

This is a KEY NOVELTY feature for the hackathon.
"""

import os
import json
import math
from typing import Optional

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class RAGEngine:
    """
    In-memory RAG engine that:
    1. Chunks code + docs into semantic segments
    2. Embeds each chunk using Gemini Embedding API
    3. On query, embeds the question and finds top-k similar chunks
    4. Augments the Gemini prompt with retrieved context
    """

    def __init__(self):
        self.chunks: list[dict] = []        # {text, metadata, embedding}
        self.is_indexed = False
        self._model = None
        self._embed_model = "models/text-embedding-004"

    def _get_model(self):
        if self._model is None:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if api_key and HAS_GEMINI:
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel("gemini-2.0-flash")
        return self._model

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts using Gemini Embedding API."""
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or not HAS_GEMINI:
            # Fallback: simple TF-IDF-like hashing for when no API key
            return [self._hash_embed(t) for t in texts]

        try:
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model=self._embed_model,
                content=texts,
                task_type="retrieval_document",
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding fallback due to: {e}")
            return [self._hash_embed(t) for t in texts]

    def _embed_query(self, text: str) -> list[float]:
        """Embed a query text."""
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or not HAS_GEMINI:
            return self._hash_embed(text)

        try:
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model=self._embed_model,
                content=text,
                task_type="retrieval_query",
            )
            return result['embedding']
        except Exception:
            return self._hash_embed(text)

    def _hash_embed(self, text: str, dim: int = 256) -> list[float]:
        """
        Simple hash-based embedding fallback.
        Creates a pseudo-embedding using character n-gram hashing.
        Not great for semantics but works for keyword matching.
        """
        vec = [0.0] * dim
        words = text.lower().split()
        for word in words:
            for i in range(len(word) - 1):
                ngram = word[i:i+2]
                h = hash(ngram) % dim
                vec[h] += 1.0

        # Normalize
        magnitude = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / magnitude for v in vec]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a)) or 1.0
        mag_b = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (mag_a * mag_b)

    def index_code(self, code: str, language: str, endpoints: list[dict]):
        """
        Index source code and parsed endpoints into the RAG store.
        
        Chunking strategy:
        1. Each endpoint gets its own chunk (with context)
        2. Code is split into logical blocks (functions/routes)
        3. Each chunk has metadata for filtering
        """
        self.chunks = []

        # ─── Chunk 1: Overall API summary ───
        endpoint_summary = []
        for ep in endpoints:
            endpoint_summary.append(f"{ep.get('method', 'GET')} {ep.get('path', '/')}")
        
        self.chunks.append({
            "text": f"This API has {len(endpoints)} endpoints: {', '.join(endpoint_summary)}",
            "metadata": {"type": "summary", "language": language},
            "embedding": None,
        })

        # ─── Chunk 2: Per-endpoint chunks ───
        for ep in endpoints:
            method = ep.get("method", "GET")
            path = ep.get("path", "/")
            func_name = ep.get("function_name", "unknown")
            docstring = ep.get("docstring", "")
            params = ep.get("parameters", [])
            body_fields = ep.get("body_fields", [])
            request_body = ep.get("request_body")

            # Build a rich text chunk for this endpoint
            chunk_text = f"Endpoint: {method} {path}\n"
            chunk_text += f"Function: {func_name}\n"
            if docstring:
                chunk_text += f"Description: {docstring}\n"
            
            if params:
                chunk_text += "Parameters:\n"
                for p in params:
                    req = "required" if p.get("required") else "optional"
                    chunk_text += f"  - {p.get('name', '?')} ({p.get('type', 'string')}, {req}, in {p.get('location', 'query')})\n"
            
            if body_fields:
                chunk_text += f"Request body fields: {', '.join(body_fields)}\n"
            elif request_body:
                if request_body.get("model"):
                    chunk_text += f"Request body model: {request_body['model']}\n"
                chunk_text += f"Content type: {request_body.get('type', 'json')}\n"

            # Determine semantic tags for better retrieval
            action_tags = []
            if method == "GET" and "id" not in path.lower():
                action_tags.extend(["list", "get all", "fetch", "read", "browse"])
            elif method == "GET":
                action_tags.extend(["get", "fetch", "read", "find", "retrieve", "lookup"])
            elif method == "POST":
                action_tags.extend(["create", "add", "new", "register", "submit", "insert"])
            elif method in ("PUT", "PATCH"):
                action_tags.extend(["update", "edit", "modify", "change", "patch"])
            elif method == "DELETE":
                action_tags.extend(["delete", "remove", "destroy", "drop"])
            
            # Extract resource name
            path_parts = [p for p in path.split("/") if p and not p.startswith("{") and not p.startswith(":") and not p.startswith("<")]
            resource = path_parts[-1] if path_parts else "resource"
            action_tags.append(resource)
            action_tags.append(resource.rstrip("s"))  # singular form
            
            chunk_text += f"Related actions: {', '.join(action_tags)}\n"

            self.chunks.append({
                "text": chunk_text,
                "metadata": {
                    "type": "endpoint",
                    "method": method,
                    "path": path,
                    "function_name": func_name,
                    "language": language,
                },
                "embedding": None,
            })

        # ─── Chunk 3: Code blocks (split by functions) ───
        code_lines = code.split("\n")
        current_block = []
        current_start = 0

        for i, line in enumerate(code_lines):
            # Detect function/route boundaries
            is_boundary = False
            stripped = line.strip()
            if language == "python" and (stripped.startswith("def ") or stripped.startswith("async def ") or stripped.startswith("@app.") or stripped.startswith("@router.")):
                is_boundary = True
            elif language == "javascript" and (stripped.startswith("app.") or stripped.startswith("router.") or "function " in stripped):
                is_boundary = True

            if is_boundary and current_block:
                block_text = "\n".join(current_block)
                if len(block_text.strip()) > 20:  # Skip tiny blocks
                    self.chunks.append({
                        "text": f"Code block (lines {current_start+1}-{i}):\n{block_text}",
                        "metadata": {"type": "code", "start_line": current_start + 1, "end_line": i},
                        "embedding": None,
                    })
                current_block = [line]
                current_start = i
            else:
                current_block.append(line)

        # Last block
        if current_block:
            block_text = "\n".join(current_block)
            if len(block_text.strip()) > 20:
                self.chunks.append({
                    "text": f"Code block (lines {current_start+1}-{len(code_lines)}):\n{block_text}",
                    "metadata": {"type": "code", "start_line": current_start + 1, "end_line": len(code_lines)},
                    "embedding": None,
                })

        # ─── Embed all chunks ───
        texts = [c["text"] for c in self.chunks]
        if texts:
            embeddings = self._embed(texts)
            for chunk, emb in zip(self.chunks, embeddings):
                chunk["embedding"] = emb
        
        self.is_indexed = True
        return {
            "chunks_indexed": len(self.chunks),
            "endpoint_chunks": sum(1 for c in self.chunks if c["metadata"]["type"] == "endpoint"),
            "code_chunks": sum(1 for c in self.chunks if c["metadata"]["type"] == "code"),
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve the most relevant chunks for a query.
        Returns top-k chunks sorted by similarity.
        """
        if not self.is_indexed or not self.chunks:
            return []

        query_embedding = self._embed_query(query)

        scored = []
        for chunk in self.chunks:
            if chunk["embedding"] is None:
                continue
            sim = self._cosine_similarity(query_embedding, chunk["embedding"])
            scored.append({
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "similarity": round(sim, 4),
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]

    def query(self, question: str, top_k: int = 5) -> dict:
        """
        Full RAG pipeline:
        1. Retrieve relevant chunks
        2. Build augmented prompt
        3. Generate answer with Gemini
        """
        retrieved = self.retrieve(question, top_k=top_k)
        
        if not retrieved:
            return {
                "answer": "No indexed data found. Please generate docs first to enable RAG.",
                "relevant_endpoints": [],
                "example_request": None,
                "rag_context": [],
            }

        # Build context from retrieved chunks
        context_parts = []
        for i, chunk in enumerate(retrieved):
            context_parts.append(f"--- Retrieved Context {i+1} (similarity: {chunk['similarity']}) ---\n{chunk['text']}")
        
        context = "\n\n".join(context_parts)

        # Extract relevant endpoints from retrieved chunks
        relevant_endpoints = []
        for chunk in retrieved:
            if chunk["metadata"].get("type") == "endpoint":
                relevant_endpoints.append({
                    "method": chunk["metadata"].get("method", ""),
                    "path": chunk["metadata"].get("path", ""),
                    "why": f"Similarity: {chunk['similarity']}"
                })

        model = self._get_model()
        if model:
            try:
                prompt = f"""You are an API documentation assistant using RAG (Retrieval Augmented Generation).
The following context was retrieved from the API's code and documentation based on the user's question.

## Retrieved Context:
{context}

## User's Question:
{question}

## Instructions:
1. Answer the question using ONLY the retrieved context above
2. Be specific — mention exact endpoint paths, methods, and parameters
3. If you can, provide a curl example
4. If the context doesn't contain enough info, say so
5. Keep the answer concise and developer-friendly

Respond in this JSON format:
{{
    "answer": "Your detailed answer here",
    "relevant_endpoints": [
        {{"method": "GET", "path": "/users", "why": "explanation"}}
    ],
    "example_request": {{
        "method": "GET",
        "url": "http://localhost:5000/users",
        "headers": {{}},
        "body": null
    }}
}}

Return ONLY valid JSON, no markdown code fences."""

                response = model.generate_content(prompt)
                text = response.text.strip()
                
                # Clean markdown fences
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                
                try:
                    result = json.loads(text)
                    result["rag_context"] = [
                        {"text": c["text"][:200], "similarity": c["similarity"], "type": c["metadata"]["type"]}
                        for c in retrieved
                    ]
                    return result
                except json.JSONDecodeError:
                    return {
                        "answer": text,
                        "relevant_endpoints": relevant_endpoints,
                        "example_request": None,
                        "rag_context": [
                            {"text": c["text"][:200], "similarity": c["similarity"], "type": c["metadata"]["type"]}
                            for c in retrieved
                        ],
                    }
            except Exception as e:
                pass

        # Fallback: return retrieved context directly
        best = retrieved[0] if retrieved else None
        answer = f"Based on semantic search, the most relevant information is:\n\n{best['text']}" if best else "No relevant information found."
        
        return {
            "answer": answer,
            "relevant_endpoints": relevant_endpoints,
            "example_request": {
                "method": relevant_endpoints[0]["method"],
                "url": f"http://localhost:5000{relevant_endpoints[0]['path']}",
                "headers": {},
                "body": None
            } if relevant_endpoints else None,
            "rag_context": [
                {"text": c["text"][:200], "similarity": c["similarity"], "type": c["metadata"]["type"]}
                for c in retrieved
            ],
        }


# Global RAG engine instance
rag_engine = RAGEngine()
