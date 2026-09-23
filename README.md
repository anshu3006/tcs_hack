# 🚀 DocuLive — AI-Powered Live API Documentation

> Paste your API code. Get beautiful docs. Test it live. All in one place.

## Features

- 🧠 **AST-Level Parsing** — Real code analysis, not regex hacking
- 📝 **AI Doc Generation** — Powered by Google Gemini
- 🏖️ **Live Sandbox** — Test every endpoint right from the docs
- 📊 **Doc Drift Score™** — Know how stale your docs are (0-100)
- 💬 **Ask Your API** — Natural language queries about your endpoints
- 🕸️ **API Graph** — Interactive force-directed visualization

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
# Optional: Create .env with your Gemini API key
# GEMINI_API_KEY=your_key_here
python main.py
```

Backend runs on http://localhost:8000

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

## Tech Stack

**Backend:** Python, FastAPI, AST module, Google Gemini API
**Frontend:** React 18, Vite, Monaco Editor, D3.js, Framer Motion

## Supported Languages

- Python (Flask, FastAPI)
- JavaScript (Express)
- OpenAPI/Swagger (YAML/JSON)

## Architecture

```
DocuLive
├── backend/           # FastAPI server
│   ├── parsers/       # AST-based code analysis
│   ├── generators/    # AI documentation generation
│   ├── analyzers/     # Drift detection & NL queries
│   └── sandbox/       # Mock server execution
└── frontend/          # React + Vite
    └── src/
        ├── components/  # UI components
        └── api.js       # Backend API client
```

## Team
Built at TCS Hackathon 2026 🏆
