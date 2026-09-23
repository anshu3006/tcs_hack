# 🚀 DocuLive — AI-Powered Live API Documentation Platform

> **One-liner pitch**: *"Paste your API code. Get beautiful docs. Test it live. All in one place."*

## The Problem (Slide 1 of Demo)

Developers waste **hours** writing API docs manually. Docs go stale. Consumers hit integration errors. Nobody reads a 200-page PDF. **DocuLive** fixes this by generating interactive, living documentation with a built-in sandbox — directly from your code.

---

## 🧠 What Makes This NOVEL (Judge-Impressor Features)

Most hackathon teams will build a "paste code → get markdown docs" tool. That's boring. Here's how we blow their minds:

### 1. 🏖️ Live API Sandbox (The Killer Feature)
- Users paste their API code (Flask/Express/FastAPI)
- We don't just generate docs — we **spin up a live sandbox** where consumers can **test every endpoint** right from the documentation page
- Think: Swagger UI on steroids, but **you don't need to deploy anything**
- Implementation: We use an **in-browser code execution sandbox** (Pyodide for Python, or a lightweight Express mock server) + a server-side Docker container fallback

### 2. 📊 Doc Drift Score™ (Original Metric)
- Upload your existing docs + your code
- We compute a **Doc Drift Score** (0-100) showing how outdated your docs are
- Highlights exactly which endpoints have drifted, what parameters changed, what's missing
- **This is our unique intellectual contribution** — no tool does this today

### 3. 🕸️ Visual API Dependency Graph
- Interactive force-directed graph showing relationships between endpoints
- Click a node → see the docs, test the endpoint, see dependencies
- Built with D3.js — looks gorgeous, feels premium

### 4. 🤖 "Ask Your API" — Natural Language Querying
- Chat interface: *"How do I create a user?"* → Returns the exact endpoint, parameters, and a pre-filled sandbox request
- Powered by Gemini API with RAG over the generated documentation

### 5. 🎯 Multi-Language AST Parsing (Not Regex!)
- We parse code using **proper AST analysis**, not fragile regex
- Supports: Python (Flask, FastAPI, Django), JavaScript (Express, Koa), and YAML/JSON OpenAPI specs
- This shows technical depth to judges

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (PC 2)                       │
│  Next.js / Vite React App — Apple-Inspired Minimal UI  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ Code     │ │ Doc      │ │ Sandbox  │ │ API Graph │ │
│  │ Editor   │ │ Viewer   │ │ Console  │ │ (D3.js)   │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘ │
│       └─────────────┴────────────┴─────────────┘       │
│                         │ REST API                       │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│                   BACKEND (PC 1)                         │
│  FastAPI Server                                         │
│  ┌──────────────┐ ┌────────────┐ ┌───────────────────┐  │
│  │ AST Parser   │ │ AI Doc Gen │ │ Doc Drift Engine  │  │
│  │ (Python/JS)  │ │ (Gemini)   │ │ (Diff + Scoring)  │  │
│  └──────────────┘ └────────────┘ └───────────────────┘  │
│  ┌──────────────┐ ┌─────────────────────────────────┐   │
│  │ NL Query     │ │ OpenAPI Spec Generator           │   │
│  │ (RAG+Gemini) │ │ (Structured JSON/YAML output)    │   │
│  └──────────────┘ └─────────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────┐
│              SANDBOX + INFRA (PC 3)                      │
│  ┌────────────────┐ ┌────────────────────────────────┐  │
│  │ Sandbox Runner │ │ Docker Container Manager       │  │
│  │ (Pyodide /     │ │ (Isolated API execution)       │  │
│  │  Mock Server)  │ │                                │  │
│  └────────────────┘ └────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ GitHub Integration (Fetch repos, parse, generate) │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 👥 3-PC Work Split

### 🖥️ PC 1 — Backend Core (The Brain)
**Owner**: Person with strongest Python skills

| Task | Time | Priority |
|------|------|----------|
| Set up FastAPI project skeleton | 5 min | 🔴 |
| Build Python AST parser (Flask/FastAPI routes) | 20 min | 🔴 |
| Build JS AST parser (Express routes) | 15 min | 🟡 |
| Integrate Gemini API for doc generation | 15 min | 🔴 |
| Build Doc Drift comparison engine | 15 min | 🔴 |
| Build NL query endpoint (Ask Your API) | 10 min | 🟡 |
| OpenAPI spec generation from parsed data | 10 min | 🟡 |
| API endpoints: `/parse`, `/generate-docs`, `/drift-score`, `/ask` | 10 min | 🔴 |

**Tech Stack**:
- Python 3.11+
- FastAPI + Uvicorn
- `ast` module (Python parsing)
- `esprima` or `acorn` via subprocess (JS parsing)
- Google Gemini API (gemini-2.0-flash)
- `difflib` for drift detection

**Git Repo Structure**:
```
backend/
├── main.py                 # FastAPI app entry
├── requirements.txt
├── parsers/
│   ├── python_parser.py    # AST-based Flask/FastAPI parser
│   ├── js_parser.py        # Express route parser
│   └── openapi_parser.py   # YAML/JSON spec parser
├── generators/
│   ├── doc_generator.py    # Gemini-powered doc generation
│   └── openapi_generator.py
├── analyzers/
│   ├── drift_detector.py   # Doc drift scoring
│   └── nl_query.py         # Natural language query handler
├── models/
│   └── schemas.py          # Pydantic models
└── sample_data/
    ├── sample_flask.py
    ├── sample_express.js
    └── sample_docs.md
```

---

### 🖥️ PC 2 — Frontend (The Face)
**Owner**: Person with strongest React/UI skills

| Task | Time | Priority |
|------|------|----------|
| Set up Vite + React project | 5 min | 🔴 |
| Build Apple-inspired design system (CSS) | 15 min | 🔴 |
| Code Editor component (Monaco Editor) | 10 min | 🔴 |
| Documentation Viewer (markdown render) | 15 min | 🔴 |
| Sandbox Console UI (request/response) | 15 min | 🔴 |
| API Dependency Graph (D3.js force graph) | 15 min | 🟡 |
| Doc Drift Score dashboard | 10 min | 🟡 |
| "Ask Your API" chat interface | 10 min | 🟡 |
| Landing page + demo flow | 10 min | 🔴 |
| Responsive polish + animations | 10 min | 🟡 |

**Tech Stack**:
- Vite + React 18
- Monaco Editor (VS Code editor in browser)
- `react-markdown` + `rehype-highlight` for doc rendering
- D3.js for the API graph
- Framer Motion for animations
- CSS Variables for Apple-style theming (SF Pro font feel)

**Git Repo Structure**:
```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── index.css              # Apple-inspired design system
│   ├── components/
│   │   ├── CodeEditor.jsx     # Monaco-based code input
│   │   ├── DocViewer.jsx      # Rendered documentation
│   │   ├── SandboxConsole.jsx # API testing sandbox
│   │   ├── ApiGraph.jsx       # D3 force-directed graph
│   │   ├── DriftScore.jsx     # Drift score gauge
│   │   ├── AskApi.jsx         # Chat interface
│   │   ├── Navbar.jsx
│   │   └── Hero.jsx           # Landing section
│   ├── hooks/
│   │   └── useApi.js          # API call hooks
│   └── utils/
│       └── constants.js
└── public/
    └── favicon.svg
```

**Apple-Inspired UI Design Principles**:
- **Color palette**: Deep blacks (#000, #1d1d1f), warm whites (#f5f5f7), accent blue (#0071e3)
- **Typography**: Inter/SF Pro-like, large hero text, generous whitespace
- **Cards**: Subtle glassmorphism with `backdrop-filter: blur(20px)`
- **Animations**: Smooth 0.3s ease transitions, scroll-triggered reveals
- **Layout**: Full-width sections, centered content, maximum 1200px

---

### 🖥️ PC 3 — Sandbox + Infrastructure (The Engine)
**Owner**: Person with DevOps/infra skills

| Task | Time | Priority |
|------|------|----------|
| Set up sandbox execution service | 15 min | 🔴 |
| Build mock server generator (from parsed routes) | 20 min | 🔴 |
| Docker container for isolated execution | 15 min | 🟡 |
| GitHub repo fetcher + parser pipeline | 15 min | 🟡 |
| WebSocket for real-time sandbox output | 10 min | 🟡 |
| CORS proxy for sandbox requests | 5 min | 🔴 |
| Integration testing all 3 services | 15 min | 🔴 |
| Demo data preparation (3 sample APIs) | 10 min | 🔴 |
| Deployment script (docker-compose) | 10 min | 🟡 |

**Tech Stack**:
- Node.js + Express (sandbox service)
- Docker (optional, for isolated execution)
- `vm2` or `isolated-vm` (safe JS execution)
- WebSocket (`ws` library)
- GitHub API (for repo fetching)

**Git Repo Structure**:
```
sandbox/
├── server.js               # Sandbox execution service
├── package.json
├── executor/
│   ├── mock_generator.js   # Generate mock API from parsed routes
│   ├── python_runner.js    # Execute Python snippets (Pyodide bridge)
│   └── js_runner.js        # Execute JS in isolated VM
├── github/
│   └── repo_fetcher.js     # Fetch and parse GitHub repos
├── websocket/
│   └── ws_handler.js       # Real-time output streaming
└── docker/
    ├── Dockerfile
    └── docker-compose.yml   # Orchestrate all 3 services
```

---

## ⏱️ 150-Minute Timeline (Mapped to TCS Schedule)

| Time | Phase | What to Do |
|------|-------|-----------|
| **0–10** | Decompose | Read this plan, assign PCs, set up Git repos |
| **10–25** | Generate Spec | Each PC reviews their task list, clarifies any questions |
| **25–35** | Break into Tasks | Each person creates their local task checklist |
| **35–65** | Build (Phase 1) | **PC1**: Parser + Gemini integration. **PC2**: Design system + editor. **PC3**: Sandbox service |
| **65–95** | Build (Phase 2) | **PC1**: Drift detector + NL query. **PC2**: Doc viewer + sandbox UI. **PC3**: Mock generator + GitHub fetcher |
| **95–105** | Integration | Git push all repos. Wire frontend ↔ backend ↔ sandbox. Fix CORS |
| **105–120** | Personal Touch | Each person adds ONE unique feature/polish they're proud of |
| **120–135** | Test & Fix | Test with 3 sample APIs. Break it. Fix the obvious bugs |
| **135–150** | Demo Prep | 3 slides. One clean run-through. Rehearse the pitch |

---

## 🎤 Demo Script (3 Slides)

### Slide 1: The Problem
> "API docs are always outdated. 67% of developers say poor docs are their #1 frustration with APIs. We built DocuLive."

### Slide 2: What We Built (Live Demo)
1. Paste a Flask API → instant beautiful docs appear
2. Click "Try It" on any endpoint → sandbox runs it live
3. Show the Doc Drift Score on a real GitHub repo
4. Ask "How do I create a user?" → get the answer with a pre-filled request

### Slide 3: Your Touch + What We Learned
- "We invented Doc Drift Score™ — a novel metric for documentation freshness"
- "We built AST-level parsing, not regex — this actually understands your code"
- "Edge case: Nested blueprint routes in Flask broke our parser. We fixed it by..."
- "Next: VS Code extension, CI/CD integration, auto-PR for doc drift > 50"

---

## 🔑 Gemini API Integration

```python
# Example: Doc generation prompt
SYSTEM_PROMPT = """You are an expert API documentation writer.
Given the following parsed API endpoint data, generate clear, concise,
developer-friendly documentation in Markdown format.

Include:
- Endpoint path and HTTP method
- Description of what it does
- Parameters (path, query, body) with types and descriptions
- Example request and response
- Error codes and their meanings

Style: Concise, professional, like Stripe's API docs."""
```

---

## 🎯 Judging Criteria Mapped

| Criteria | How We Address It |
|----------|------------------|
| **Did you build it?** | Live running app with 3 services. Demo: paste code → get docs → test in sandbox |
| **Did you use AI deliberately?** | Gemini for doc generation + NL query. AST parsing is rule-based (deliberate choice — AI for creative writing, rules for structure) |
| **Is your touch visible?** | Doc Drift Score™ is our invention. Apple UI is our design choice. Sandbox is our architectural decision |
| **Did you test it?** | 3 sample APIs tested. Edge cases: empty routes, async handlers, nested blueprints |

---

## ⚠️ User Review Required

> [!IMPORTANT]
> **API Key Required**: You need a Google Gemini API key. Do you have one, or should we use a free tier? 
> The free tier of `gemini-2.0-flash` should be sufficient for a hackathon demo.

> [!IMPORTANT]
> **Prerequisites on the 3 PCs**: 
> - All PCs need: Node.js 18+, Python 3.11+, Git
> - PC 3 additionally needs: Docker Desktop (optional but nice)
> - Do all PCs have these installed?

> [!WARNING]
> **Network dependency**: The Gemini API requires internet. Make sure the hackathon venue has stable WiFi.
> As a fallback, we can pre-generate docs for sample APIs and cache them.

## Open Questions

1. **Which languages do your 3 team members prefer?** (Python / JavaScript / Both?)
2. **Do you have a Gemini API key?** If not, I'll set up the free tier
3. **Do all 3 PCs have Docker?** If not, we'll skip containerized sandbox and use in-process execution
4. **How much time do you have?** The slides say 150 min — is that your total time including planning?
5. **Should I start building the code now?** If yes, which PC am I building for (PC1, PC2, or PC3)?

## Verification Plan

### Automated Tests
- Backend: Test each parser with sample Flask/Express code → verify extracted routes match expected
- Frontend: Visual verification in browser
- Sandbox: Test mock server generation → verify endpoints respond correctly

### Manual Verification
- End-to-end flow: Paste code → docs generated → sandbox works → drift score calculated
- Test with 3 different API frameworks
- Test error cases: invalid code, empty file, missing routes
