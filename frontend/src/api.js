const API_BASE = '/api';

export async function parseCode(code, language = 'python', framework = 'auto') {
  const res = await fetch(`${API_BASE}/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language, framework }),
  });
  if (!res.ok) throw new Error(`Parse failed: ${res.statusText}`);
  return res.json();
}

export async function generateDocs(code, language = 'python', framework = 'auto', style = 'stripe') {
  const res = await fetch(`${API_BASE}/generate-docs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, language, framework, style }),
  });
  if (!res.ok) throw new Error(`Generation failed: ${res.statusText}`);
  return res.json();
}

export async function computeDrift(code, existingDocs, language = 'python', framework = 'auto') {
  const res = await fetch(`${API_BASE}/drift-score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, existing_docs: existingDocs, language, framework }),
  });
  if (!res.ok) throw new Error(`Drift analysis failed: ${res.statusText}`);
  return res.json();
}

export async function askApi(question, code, language = 'python', framework = 'auto') {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, code, language, framework }),
  });
  if (!res.ok) throw new Error(`Query failed: ${res.statusText}`);
  return res.json();
}

export async function executeSandbox(code, endpoint, method = 'GET', body = null) {
  const res = await fetch(`${API_BASE}/sandbox/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, endpoint, method, body }),
  });
  if (!res.ok) throw new Error(`Sandbox failed: ${res.statusText}`);
  return res.json();
}

export async function getSamples() {
  const res = await fetch(`${API_BASE}/samples`);
  if (!res.ok) throw new Error(`Failed to load samples: ${res.statusText}`);
  return res.json();
}

export async function fetchGitHub(repoUrl) {
  const res = await fetch(`${API_BASE}/github/fetch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: repoUrl }),
  });
  if (!res.ok) throw new Error(`GitHub fetch failed: ${res.statusText}`);
  return res.json();
}
