import { useState, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { generateDocs, computeDrift, askApi, executeSandbox, getSamples } from './api';
import CodeEditor from './components/CodeEditor';
import DocViewer from './components/DocViewer';
import SandboxConsole from './components/SandboxConsole';
import DriftScore from './components/DriftScore';
import AskApiChat from './components/AskApiChat';
import ApiGraph from './components/ApiGraph';

const SAMPLE_FLASK = `from flask import Flask, request, jsonify

app = Flask(__name__)

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
    }
    users.append(user)
    return jsonify(user), 201`;

const VIEWS = [
  { id: 'generate', label: 'Generate Docs', icon: '📝' },
  { id: 'sandbox', label: 'Sandbox', icon: '🏖️' },
  { id: 'drift', label: 'Drift Score', icon: '📊' },
  { id: 'ask', label: 'Ask API', icon: '💬' },
  { id: 'graph', label: 'API Graph', icon: '🕸️' },
];

export default function App() {
  const [code, setCode] = useState(SAMPLE_FLASK);
  const [language, setLanguage] = useState('python');
  const [activeView, setActiveView] = useState('generate');
  const [showSamples, setShowSamples] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Results state
  const [generatedDocs, setGeneratedDocs] = useState(null);
  const [parsedEndpoints, setParsedEndpoints] = useState([]);
  const [openApiSpec, setOpenApiSpec] = useState(null);
  const [driftResult, setDriftResult] = useState(null);
  const [existingDocs, setExistingDocs] = useState('');
  const [toasts, setToasts] = useState([]);

  const workspaceRef = useRef(null);

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  }, []);

  const handleGenerate = async () => {
    if (!code.trim()) {
      addToast('Please enter some API code first', 'error');
      return;
    }
    setIsGenerating(true);
    try {
      const result = await generateDocs(code, language);
      setGeneratedDocs(result.markdown);
      setParsedEndpoints(result.parsed_endpoints || []);
      setOpenApiSpec(result.openapi_spec);
      addToast(`✨ Generated docs for ${result.endpoints_documented} endpoints`, 'success');
    } catch (err) {
      addToast(`Error: ${err.message}`, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSampleSelect = (sample) => {
    setCode(sample.code);
    setLanguage(sample.language);
    setShowSamples(false);
    addToast(`Loaded: ${sample.name}`, 'info');
  };

  const scrollToWorkspace = () => {
    workspaceRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const samples = [
    { name: 'Flask Blog API', language: 'python', description: 'CRUD blog with users & comments', code: SAMPLE_FLASK },
    { name: 'Express E-Commerce', language: 'javascript', description: 'Products & orders API', code: `const express = require("express");
const app = express();
app.use(express.json());

let products = [];
let orders = [];

// Get all products with filtering
app.get("/api/products", (req, res) => {
    const { category, min_price, max_price } = req.query;
    let result = [...products];
    if (category) result = result.filter(p => p.category === category);
    res.json({ data: result, total: result.length });
});

// Get single product
app.get("/api/products/:id", (req, res) => {
    const product = products.find(p => p.id === parseInt(req.params.id));
    if (!product) return res.status(404).json({ error: "Not found" });
    res.json(product);
});

// Create a product
app.post("/api/products", (req, res) => {
    const { name, price, description, category, stock } = req.body;
    const product = { id: products.length + 1, name, price, description, category, stock };
    products.push(product);
    res.status(201).json(product);
});

// Update product
app.put("/api/products/:id", (req, res) => {
    const { name, price, description } = req.body;
    const product = products.find(p => p.id === parseInt(req.params.id));
    if (!product) return res.status(404).json({ error: "Not found" });
    Object.assign(product, req.body);
    res.json(product);
});

// Delete product
app.delete("/api/products/:id", (req, res) => {
    products = products.filter(p => p.id !== parseInt(req.params.id));
    res.json({ message: "Deleted" });
});

// Create order
app.post("/api/orders", (req, res) => {
    const { user_id, product_ids, shipping_address } = req.body;
    const order = { id: orders.length + 1, user_id, product_ids, shipping_address, status: "pending" };
    orders.push(order);
    res.status(201).json(order);
});

// Get order
app.get("/api/orders/:id", (req, res) => {
    const order = orders.find(o => o.id === parseInt(req.params.id));
    if (!order) return res.status(404).json({ error: "Not found" });
    res.json(order);
});

app.listen(3000);` },
    { name: 'FastAPI Users', language: 'python', description: 'User management microservice', code: `from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="User Service")

class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "member"

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

users_db = []

@app.get("/api/users")
async def list_users(skip: int = Query(0), limit: int = Query(20), role: Optional[str] = None):
    """List all users with pagination and filtering."""
    result = users_db[skip:skip + limit]
    if role:
        result = [u for u in result if u.get("role") == role]
    return {"data": result, "total": len(users_db)}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by ID."""
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
    """Update user information."""
    if user_id < 1 or user_id > len(users_db):
        raise HTTPException(404, "User not found")
    existing = users_db[user_id - 1]
    existing.update(user.model_dump(exclude_unset=True))
    return existing

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user account."""
    if user_id < 1 or user_id > len(users_db):
        raise HTTPException(404, "User not found")
    users_db.pop(user_id - 1)
    return {"message": "User deleted"}` },
  ];

  return (
    <div className="app">
      {/* ── Navbar ── */}
      <nav className="navbar">
        <a href="#" className="navbar-brand" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
          <span className="logo-icon">D</span>
          DocuLive
        </a>
        <div className="navbar-nav">
          {VIEWS.map(v => (
            <button
              key={v.id}
              className={`nav-btn ${activeView === v.id ? 'active' : ''}`}
              onClick={() => { setActiveView(v.id); scrollToWorkspace(); }}
            >
              {v.icon} {v.label}
            </button>
          ))}
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-badge">
          <span className="dot"></span>
          AI-Powered Documentation
        </div>
        <h1>
          Paste Code.<br />
          <span className="gradient-text">Get Live Docs.</span>
        </h1>
        <p className="hero-subtitle">
          DocuLive generates beautiful API documentation from your code using AST analysis and AI — with a built-in sandbox to test every endpoint.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary" onClick={scrollToWorkspace}>
            ⚡ Start Generating
          </button>
          <div className="samples-dropdown">
            <button className="btn btn-secondary" onClick={() => setShowSamples(!showSamples)}>
              📂 Load Sample
            </button>
            {showSamples && (
              <div className="samples-menu">
                {samples.map((s, i) => (
                  <div key={i} className="sample-item" onClick={() => handleSampleSelect(s)}>
                    <span className="sample-name">{s.name}</span>
                    <span className="sample-desc">{s.description}</span>
                    <span className="sample-lang">{s.language}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── Feature Pills ── */}
      <div className="features-strip">
        <div className="feature-pill"><span className="pill-icon">🧠</span> AST-Level Parsing</div>
        <div className="feature-pill"><span className="pill-icon">🏖️</span> Live Sandbox</div>
        <div className="feature-pill"><span className="pill-icon">📊</span> Doc Drift Score™</div>
        <div className="feature-pill"><span className="pill-icon">💬</span> Ask Your API</div>
        <div className="feature-pill"><span className="pill-icon">🕸️</span> API Graph</div>
        <div className="feature-pill"><span className="pill-icon">🤖</span> Gemini AI</div>
      </div>

      {/* ── Workspace ── */}
      <section className="workspace" ref={workspaceRef} id="workspace">
        <div className="workspace-header">
          <h2>workspace</h2>
          <div className="workspace-controls">
            <select
              className="lang-select"
              value={language}
              onChange={e => setLanguage(e.target.value)}
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="openapi">OpenAPI Spec</option>
            </select>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              {isGenerating ? (
                <><span className="spinner" style={{width:14,height:14,borderWidth:2}}></span> Generating...</>
              ) : (
                '⚡ Generate Docs'
              )}
            </button>
          </div>
        </div>

        {activeView === 'generate' && (
          <div className="split-view">
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>📝 Source Code</h3>
                <span style={{fontSize:'0.75rem',color:'var(--text-tertiary)',fontFamily:'var(--font-mono)'}}>
                  {language}
                </span>
              </div>
              <div className="glass-card-body no-pad">
                <CodeEditor code={code} onChange={setCode} language={language} />
              </div>
            </div>
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>📖 Documentation</h3>
                {generatedDocs && (
                  <span style={{fontSize:'0.75rem',color:'var(--accent-green)'}}>
                    ✅ {parsedEndpoints.length} endpoints
                  </span>
                )}
              </div>
              <div className="glass-card-body">
                {generatedDocs ? (
                  <DocViewer content={generatedDocs} />
                ) : (
                  <div className="empty-state">
                    <span className="empty-icon">📖</span>
                    <h3>No documentation yet</h3>
                    <p>Click "Generate Docs" or paste your API code and hit ⚡</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeView === 'sandbox' && (
          <div className="split-view">
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>📝 Source Code</h3>
              </div>
              <div className="glass-card-body no-pad">
                <CodeEditor code={code} onChange={setCode} language={language} />
              </div>
            </div>
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>🏖️ API Sandbox</h3>
              </div>
              <div className="glass-card-body">
                <SandboxConsole
                  code={code}
                  language={language}
                  endpoints={parsedEndpoints}
                  onGenerate={handleGenerate}
                />
              </div>
            </div>
          </div>
        )}

        {activeView === 'drift' && (
          <div className="split-view">
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>📝 Your Code + Existing Docs</h3>
              </div>
              <div className="glass-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{fontSize:'0.75rem',fontWeight:600,color:'var(--text-tertiary)',textTransform:'uppercase',letterSpacing:'0.06em',display:'block',marginBottom:'8px'}}>
                    API Source Code
                  </label>
                  <CodeEditor code={code} onChange={setCode} language={language} height="250px" />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{fontSize:'0.75rem',fontWeight:600,color:'var(--text-tertiary)',textTransform:'uppercase',letterSpacing:'0.06em',display:'block',marginBottom:'8px'}}>
                    Existing Documentation (paste your current docs)
                  </label>
                  <textarea
                    className="sandbox-input"
                    style={{ height: '200px', fontFamily: 'var(--font-mono)' }}
                    placeholder={`Paste your existing API documentation here...

Example:
## GET /api/posts
Returns all blog posts.

## POST /api/posts
Creates a new blog post.
Required fields: title, content`}
                    value={existingDocs}
                    onChange={e => setExistingDocs(e.target.value)}
                  />
                </div>
                <button className="btn btn-primary" onClick={async () => {
                  if (!code.trim() || !existingDocs.trim()) {
                    addToast('Please provide both code and existing docs', 'error');
                    return;
                  }
                  try {
                    const result = await computeDrift(code, existingDocs, language);
                    setDriftResult(result);
                    addToast(`Drift Score: ${result.drift_score}/100`, 'info');
                  } catch (err) {
                    addToast(`Error: ${err.message}`, 'error');
                  }
                }}>
                  📊 Analyze Drift
                </button>
              </div>
            </div>
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>📊 Doc Drift Score™</h3>
              </div>
              <div className="glass-card-body">
                <DriftScore result={driftResult} />
              </div>
            </div>
          </div>
        )}

        {activeView === 'ask' && (
          <div className="split-view">
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>📝 Source Code</h3>
              </div>
              <div className="glass-card-body no-pad">
                <CodeEditor code={code} onChange={setCode} language={language} />
              </div>
            </div>
            <div className="glass-card">
              <div className="glass-card-header">
                <h3>💬 Ask Your API</h3>
              </div>
              <div className="glass-card-body">
                <AskApiChat code={code} language={language} />
              </div>
            </div>
          </div>
        )}

        {activeView === 'graph' && (
          <div className="glass-card" style={{ minHeight: '600px' }}>
            <div className="glass-card-header">
              <h3>🕸️ API Dependency Graph</h3>
              {parsedEndpoints.length === 0 && (
                <button className="btn btn-primary btn-sm" onClick={handleGenerate}>
                  ⚡ Parse Code First
                </button>
              )}
            </div>
            <div className="glass-card-body no-pad" style={{ height: 'calc(100% - 52px)' }}>
              <ApiGraph endpoints={parsedEndpoints} />
            </div>
          </div>
        )}
      </section>

      {/* ── Toasts ── */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}
