"""
DocuLive Backend — FastAPI Server
AI-Powered Live API Documentation Platform
"""

import os
import json
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models.schemas import (
    ParseRequest, GenerateDocsRequest, DriftRequest,
    AskApiRequest, SandboxRequest, GitHubFetchRequest,
)
from parsers.python_parser import parse_python_code
from parsers.js_parser import parse_js_code
from parsers.openapi_parser import parse_openapi_spec
from generators.doc_generator import generate_docs_with_ai, generate_openapi_spec
from analyzers.drift_detector import compute_drift_score, ai_drift_analysis
from analyzers.nl_query import ask_api
from sandbox.executor import generate_mock_responses, execute_sandbox_request


# In-memory cache for sandbox mocks (per-session)
sandbox_cache: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan handler."""
    print("🚀 DocuLive Backend starting...")
    print(f"   Gemini API: {'✅ Configured' if os.getenv('GEMINI_API_KEY') else '⚠️  Not configured (using fallback)'}")
    yield
    print("👋 DocuLive Backend shutting down...")


app = FastAPI(
    title="DocuLive API",
    description="AI-Powered Live API Documentation Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "DocuLive API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "AST-based code parsing",
            "AI documentation generation",
            "Doc Drift Score™",
            "Live API Sandbox",
            "Natural language querying",
        ]
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))}


# ─── PARSE ENDPOINTS ───────────────────────────────────────────

@app.post("/api/parse")
async def parse_code(request: ParseRequest):
    """Parse API code and extract endpoint information using AST analysis."""
    try:
        if request.language == "python":
            result = parse_python_code(request.code, request.framework)
        elif request.language == "javascript":
            result = parse_js_code(request.code, request.framework)
        elif request.language == "openapi":
            result = parse_openapi_spec(request.code)
        else:
            raise HTTPException(400, f"Unsupported language: {request.language}")
        
        return result
    except Exception as e:
        raise HTTPException(500, f"Parse error: {str(e)}")


# ─── GENERATE DOCS ─────────────────────────────────────────────

@app.post("/api/generate-docs")
async def generate_docs(request: GenerateDocsRequest):
    """Generate beautiful API documentation from code."""
    try:
        # First parse the code
        if request.language == "python":
            parsed = parse_python_code(request.code, request.framework)
        elif request.language == "javascript":
            parsed = parse_js_code(request.code, request.framework)
        elif request.language == "openapi":
            parsed = parse_openapi_spec(request.code)
        else:
            raise HTTPException(400, f"Unsupported language: {request.language}")
        
        endpoints = parsed.get("endpoints", [])
        
        if not endpoints:
            return {
                "markdown": "# No Endpoints Found\n\nNo API endpoints were detected in the provided code. Make sure your code defines routes using Flask, FastAPI, or Express patterns.",
                "openapi_spec": None,
                "endpoints_documented": 0,
                "parsed_endpoints": endpoints,
            }
        
        # Generate docs with AI
        markdown = generate_docs_with_ai(endpoints, request.code, request.style)
        
        # Generate OpenAPI spec
        openapi_spec = generate_openapi_spec(endpoints)
        
        # Generate sandbox mocks
        mocks = generate_mock_responses(endpoints)
        sandbox_cache["latest"] = mocks
        
        return {
            "markdown": markdown,
            "openapi_spec": openapi_spec,
            "endpoints_documented": len(endpoints),
            "parsed_endpoints": endpoints,
            "sandbox_ready": True,
        }
    except Exception as e:
        raise HTTPException(500, f"Generation error: {str(e)}")


# ─── DOC DRIFT ──────────────────────────────────────────────────

@app.post("/api/drift-score")
async def drift_score(request: DriftRequest):
    """Compute the Doc Drift Score™ between code and existing docs."""
    try:
        # Parse the code
        if request.language == "python":
            parsed = parse_python_code(request.code, request.framework)
        elif request.language == "javascript":
            parsed = parse_js_code(request.code, request.framework)
        else:
            raise HTTPException(400, f"Unsupported language: {request.language}")
        
        endpoints = parsed.get("endpoints", [])
        
        # Compute drift
        drift_result = compute_drift_score(endpoints, request.existing_docs)
        
        # Get AI analysis
        analysis = ai_drift_analysis(drift_result, request.code, request.existing_docs)
        drift_result["ai_analysis"] = analysis
        
        return drift_result
    except Exception as e:
        raise HTTPException(500, f"Drift analysis error: {str(e)}")


# ─── ASK YOUR API ──────────────────────────────────────────────

@app.post("/api/ask")
async def ask_api_endpoint(request: AskApiRequest):
    """Ask a natural language question about the API."""
    try:
        # Parse the code first
        if request.language == "python":
            parsed = parse_python_code(request.code, request.framework)
        elif request.language == "javascript":
            parsed = parse_js_code(request.code, request.framework)
        else:
            raise HTTPException(400, f"Unsupported language: {request.language}")
        
        endpoints = parsed.get("endpoints", [])
        
        result = ask_api(request.question, endpoints, request.code)
        return result
    except Exception as e:
        raise HTTPException(500, f"Query error: {str(e)}")


# ─── SANDBOX ────────────────────────────────────────────────────

@app.post("/api/sandbox/execute")
async def sandbox_execute(request: SandboxRequest):
    """Execute a request in the sandbox environment."""
    try:
        # Always parse and generate fresh mocks based on the provided code
        # to ensure it matches the current frontend state.
        parsed = parse_python_code(request.code)
        if not parsed.get("endpoints"):
            parsed = parse_js_code(request.code)
        mocks = generate_mock_responses(parsed.get("endpoints", []))
        
        result = execute_sandbox_request(
            mocks=mocks,
            endpoint=request.endpoint,
            method=request.method,
            body=request.body,
            headers=request.headers,
            query_params=request.query_params,
        )
        
        return result
    except Exception as e:
        raise HTTPException(500, f"Sandbox error: {str(e)}")


@app.post("/api/sandbox/generate-mocks")
async def generate_sandbox_mocks(request: ParseRequest):
    """Generate mock responses for parsed endpoints."""
    try:
        if request.language == "python":
            parsed = parse_python_code(request.code, request.framework)
        elif request.language == "javascript":
            parsed = parse_js_code(request.code, request.framework)
        else:
            raise HTTPException(400, f"Unsupported language: {request.language}")
        
        endpoints = parsed.get("endpoints", [])
        mocks = generate_mock_responses(endpoints)
        sandbox_cache["latest"] = mocks
        
        return {
            "mocks": mocks,
            "total_endpoints": len(endpoints),
        }
    except Exception as e:
        raise HTTPException(500, f"Mock generation error: {str(e)}")


# ─── GITHUB INTEGRATION ────────────────────────────────────────

@app.post("/api/github/fetch")
async def fetch_github_repo(request: GitHubFetchRequest):
    """Fetch and parse API code from a public GitHub repository."""
    import httpx
    
    try:
        # Convert GitHub URL to raw content URL
        url = request.repo_url.strip()
        
        # Handle different GitHub URL formats
        if "github.com" in url:
            # Convert to API URL
            url = url.replace("github.com", "raw.githubusercontent.com")
            url = url.replace("/blob/", "/")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=10.0)
            response.raise_for_status()
            code = response.text
        
        # Auto-detect language
        if url.endswith(".py"):
            language = "python"
        elif url.endswith((".js", ".ts")):
            language = "javascript"
        elif url.endswith((".yaml", ".yml", ".json")):
            language = "openapi"
        else:
            language = "python"  # default
        
        return {
            "code": code,
            "language": language,
            "source": request.repo_url,
        }
    except httpx.HTTPError as e:
        raise HTTPException(400, f"Could not fetch from GitHub: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"GitHub fetch error: {str(e)}")


# ─── SAMPLE DATA ────────────────────────────────────────────────

@app.get("/api/samples")
async def get_samples():
    """Return sample code snippets for demo purposes."""
    return {
        "samples": [
            {
                "name": "Flask Blog API",
                "language": "python",
                "framework": "flask",
                "description": "A blog API with CRUD operations",
                "code": SAMPLE_FLASK,
            },
            {
                "name": "Express E-Commerce API",
                "language": "javascript",
                "framework": "express",
                "description": "An e-commerce API with products and orders",
                "code": SAMPLE_EXPRESS,
            },
            {
                "name": "FastAPI User Service",
                "language": "python",
                "framework": "fastapi",
                "description": "A user management microservice",
                "code": SAMPLE_FASTAPI,
            },
        ]
    }


# ─── SAMPLE CODE SNIPPETS ──────────────────────────────────────

SAMPLE_FLASK = '''from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage
posts = []
users = []

@app.route("/api/posts", methods=["GET"])
def get_posts():
    """Get all blog posts with optional filtering."""
    category = request.args.get("category")
    limit = request.args.get("limit", 20, type=int)
    if category:
        filtered = [p for p in posts if p.get("category") == category]
        return jsonify(filtered[:limit])
    return jsonify(posts[:limit])

@app.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    """Get a single blog post by ID."""
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post)

@app.route("/api/posts", methods=["POST"])
def create_post():
    """Create a new blog post."""
    data = request.json
    post = {
        "id": len(posts) + 1,
        "title": data.get("title"),
        "content": data.get("content"),
        "author": data.get("author"),
        "category": data.get("category", "general"),
    }
    posts.append(post)
    return jsonify(post), 201

@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    """Update an existing blog post."""
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    data = request.json
    post.update(data)
    return jsonify(post)

@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """Delete a blog post."""
    global posts
    posts = [p for p in posts if p["id"] != post_id]
    return jsonify({"message": "Post deleted"}), 200

@app.route("/api/users", methods=["GET"])
def get_users():
    """List all registered users."""
    return jsonify(users)

@app.route("/api/users", methods=["POST"])
def create_user():
    """Register a new user."""
    data = request.json
    user = {
        "id": len(users) + 1,
        "name": data.get("name"),
        "email": data.get("email"),
        "role": data.get("role", "reader"),
    }
    users.append(user)
    return jsonify(user), 201

@app.route("/api/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    """Get all comments for a specific post."""
    return jsonify([])

@app.route("/api/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    """Add a comment to a blog post."""
    data = request.json
    comment = {
        "id": 1,
        "post_id": post_id,
        "text": data.get("text"),
        "author": data.get("author"),
    }
    return jsonify(comment), 201
'''

SAMPLE_EXPRESS = '''const express = require("express");
const app = express();
app.use(express.json());

let products = [];
let orders = [];

// Get all products with filtering
app.get("/api/products", (req, res) => {
    const { category, min_price, max_price, sort } = req.query;
    let result = [...products];
    if (category) result = result.filter(p => p.category === category);
    if (min_price) result = result.filter(p => p.price >= parseFloat(min_price));
    if (max_price) result = result.filter(p => p.price <= parseFloat(max_price));
    res.json({ data: result, total: result.length });
});

// Get single product by ID
app.get("/api/products/:id", (req, res) => {
    const product = products.find(p => p.id === parseInt(req.params.id));
    if (!product) return res.status(404).json({ error: "Product not found" });
    res.json(product);
});

// Create a new product
app.post("/api/products", (req, res) => {
    const { name, price, description, category, stock } = req.body;
    const product = {
        id: products.length + 1,
        name, price, description, category, stock,
        created_at: new Date().toISOString()
    };
    products.push(product);
    res.status(201).json(product);
});

// Update a product
app.put("/api/products/:id", (req, res) => {
    const { name, price, description, category, stock } = req.body;
    const product = products.find(p => p.id === parseInt(req.params.id));
    if (!product) return res.status(404).json({ error: "Product not found" });
    Object.assign(product, req.body);
    res.json(product);
});

// Delete a product
app.delete("/api/products/:id", (req, res) => {
    products = products.filter(p => p.id !== parseInt(req.params.id));
    res.json({ message: "Product deleted" });
});

// Create an order
app.post("/api/orders", (req, res) => {
    const { user_id, product_ids, shipping_address } = req.body;
    const order = {
        id: orders.length + 1,
        user_id, product_ids, shipping_address,
        status: "pending",
        created_at: new Date().toISOString()
    };
    orders.push(order);
    res.status(201).json(order);
});

// Get order by ID
app.get("/api/orders/:id", (req, res) => {
    const order = orders.find(o => o.id === parseInt(req.params.id));
    if (!order) return res.status(404).json({ error: "Order not found" });
    res.json(order);
});

// Update order status
app.patch("/api/orders/:id/status", (req, res) => {
    const { status } = req.body;
    const order = orders.find(o => o.id === parseInt(req.params.id));
    if (!order) return res.status(404).json({ error: "Order not found" });
    order.status = status;
    res.json(order);
});

app.listen(3000);
'''

SAMPLE_FASTAPI = '''from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List

app = FastAPI(title="User Service", version="2.0.0")

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "member"
    department: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None

users_db = []

@app.get("/api/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    department: Optional[str] = None,
):
    """List all users with pagination and optional filtering by role or department."""
    result = users_db[skip:skip + limit]
    if role:
        result = [u for u in result if u.get("role") == role]
    if department:
        result = [u for u in result if u.get("department") == department]
    return {"data": result, "total": len(users_db), "skip": skip, "limit": limit}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by their ID."""
    if user_id < 1 or user_id > len(users_db):
        raise HTTPException(404, "User not found")
    return users_db[user_id - 1]

@app.post("/api/users", status_code=201)
async def create_user(user: UserCreate):
    """Create a new user account."""
    user_dict = user.model_dump()
    user_dict["id"] = len(users_db) + 1
    users_db.append(user_dict)
    return user_dict

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user: UserUpdate):
    """Update an existing user\'s information."""
    if user_id < 1 or user_id > len(users_db):
        raise HTTPException(404, "User not found")
    existing = users_db[user_id - 1]
    update_data = user.model_dump(exclude_unset=True)
    existing.update(update_data)
    return existing

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user account. This action is irreversible."""
    if user_id < 1 or user_id > len(users_db):
        raise HTTPException(404, "User not found")
    users_db.pop(user_id - 1)
    return {"message": "User deleted successfully"}

@app.get("/api/users/{user_id}/activity")
async def get_user_activity(user_id: int, days: int = Query(30, ge=1, le=365)):
    """Get activity log for a specific user."""
    return {"user_id": user_id, "activities": [], "period_days": days}

@app.post("/api/users/bulk")
async def bulk_create_users(users: List[UserCreate]):
    """Create multiple user accounts at once."""
    created = []
    for user in users:
        user_dict = user.model_dump()
        user_dict["id"] = len(users_db) + 1
        users_db.append(user_dict)
        created.append(user_dict)
    return {"created": len(created), "users": created}
'''


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
