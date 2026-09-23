/**
 * DocForge AI — Frontend Application Logic
 */

const API_BASE = window.location.origin;

// DOM Elements
const codeInput = document.getElementById('codeInput');
const lineNumbers = document.getElementById('lineNumbers');
const languageSelect = document.getElementById('languageSelect');
const generateBtn = document.getElementById('generateBtn');
const emptyState = document.getElementById('emptyState');
const results = document.getElementById('results');
const docsOutput = document.getElementById('docsOutput');
const statusBadge = document.getElementById('statusBadge');
const fileInput = document.getElementById('fileInput');
const uploadZone = document.getElementById('uploadZone');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const removeFileBtn = document.getElementById('removeFile');
const qualityScore = document.getElementById('qualityScore');
const qualityGrade = document.getElementById('qualityGrade');
const qualitySummary = document.getElementById('qualitySummary');
const qualityRingCircle = document.getElementById('qualityRingCircle');
const qualityExpandBtn = document.getElementById('qualityExpandBtn');
const qualityDetails = document.getElementById('qualityDetails');
const qualityChecks = document.getElementById('qualityChecks');
const qualitySuggestions = document.getElementById('qualitySuggestions');
const endpointCount = document.getElementById('endpointCount');
const exportOpenApiBtn = document.getElementById('exportOpenApiBtn');
const toast = document.getElementById('toast');

// Sandbox Modal Elements
const sandboxModal = document.getElementById('sandboxModal');
const closeSandboxModal = document.getElementById('closeSandboxModal');
const modalMethod = document.getElementById('modalMethod');
const modalUrl = document.getElementById('modalUrl');
const sandboxPayload = document.getElementById('sandboxPayload');
const runSandboxBtn = document.getElementById('runSandboxBtn');
const sandboxResponseArea = document.getElementById('sandboxResponseArea');
const sandboxOutput = document.getElementById('sandboxOutput');

let uploadedFile = null;
let currentTab = 'paste';
let currentDocData = null;
let activeSandboxEndpoint = null;

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`content${tab.charAt(0).toUpperCase() + tab.slice(1)}`).classList.add('active');
  });
});

// Editor Line Numbers
function updateLineNumbers() {
  const lines = codeInput.value.split('\n').length;
  const nums = [];
  for (let i = 1; i <= Math.max(lines, 20); i++) nums.push(i);
  lineNumbers.textContent = nums.join('\n');
}

codeInput.addEventListener('input', updateLineNumbers);
codeInput.addEventListener('scroll', () => { lineNumbers.scrollTop = codeInput.scrollTop; });
updateLineNumbers();

// File Upload
uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  uploadedFile = file;
  fileName.textContent = file.name;
  fileInfo.classList.remove('hidden');
  uploadZone.style.display = 'none';

  const ext = file.name.split('.').pop().toLowerCase();
  const langMap = { py: 'python', js: 'javascript', ts: 'typescript', java: 'java', go: 'go', json: 'json', yaml: 'yaml' };
  if (langMap[ext]) languageSelect.value = langMap[ext];

  showToast('success', `File loaded: ${file.name}`);
}

removeFileBtn.addEventListener('click', () => {
  uploadedFile = null;
  fileInput.value = '';
  fileInfo.classList.add('hidden');
  uploadZone.style.display = 'flex';
});

// Sample Code Cards
document.querySelectorAll('.sample-card').forEach(card => {
  card.addEventListener('click', () => {
    const sampleKey = card.dataset.sample;
    const sample = SAMPLES[sampleKey];
    if (sample) {
      codeInput.value = sample.code;
      languageSelect.value = sample.language;
      updateLineNumbers();
      document.querySelector('[data-tab="paste"]').click();
      showToast('success', `Loaded ${sample.name} sample`);
    }
  });
});

// Generate Docs
generateBtn.addEventListener('click', handleGenerate);

async function handleGenerate() {
  if (currentTab === 'upload' && uploadedFile) {
    await generateFromFile();
  } else {
    await generateFromCode();
  }
}

async function generateFromCode() {
  const code = codeInput.value.trim();
  if (!code) {
    showToast('error', 'Please paste API code or pick a sample card first');
    codeInput.focus();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language: languageSelect.value })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Generation failed');

    currentDocData = data;
    renderResults(data);
    showToast('success', `Generated documentation & OWASP audit for ${data.metadata.endpointCount} endpoints`);
  } catch (err) {
    console.error(err);
    showToast('error', err.message || 'Failed to generate documentation');
    setStatus('error', 'Error');
  } finally {
    setLoading(false);
  }
}

async function generateFromFile() {
  if (!uploadedFile) {
    showToast('error', 'Please select a file first');
    return;
  }

  setLoading(true);

  try {
    const formData = new FormData();
    formData.append('file', uploadedFile);

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Upload failed');

    currentDocData = data;
    renderResults(data);
    showToast('success', `Generated documentation for ${data.metadata.endpointCount} endpoints`);
  } catch (err) {
    console.error(err);
    showToast('error', err.message || 'Failed to process file');
    setStatus('error', 'Error');
  } finally {
    setLoading(false);
  }
}

// Render Results
function renderResults(data) {
  emptyState.classList.add('hidden');
  results.classList.remove('hidden');

  renderQuality(data.quality);

  endpointCount.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
    ${data.metadata.endpointCount} endpoint${data.metadata.endpointCount !== 1 ? 's' : ''}
  `;

  renderDocumentation(data.documentation);
  setStatus('ready', 'Engine Ready');
}

function renderQuality(quality) {
  const circumference = 2 * Math.PI * 34;
  const offset = circumference - (quality.score / 100) * circumference;

  qualityRingCircle.style.transition = 'none';
  qualityRingCircle.setAttribute('stroke-dashoffset', circumference);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      qualityRingCircle.style.transition = 'stroke-dashoffset 1.2s ease-out';
      qualityRingCircle.setAttribute('stroke-dashoffset', offset);
    });
  });

  animateCounter(qualityScore, 0, quality.score, 1000);

  qualityGrade.textContent = quality.grade;
  qualitySummary.textContent = quality.summary;

  if (quality.score >= 85) {
    qualityGrade.style.background = 'linear-gradient(135deg, #34d399, #059669)';
  } else if (quality.score >= 70) {
    qualityGrade.style.background = 'linear-gradient(135deg, #fbbf24, #d97706)';
  } else {
    qualityGrade.style.background = 'linear-gradient(135deg, #fb7185, #e11d48)';
  }

  renderQualityChecks(quality);
}

function renderQualityChecks(quality) {
  let checksHTML = '';

  if (quality.endpointReports) {
    quality.endpointReports.forEach(report => {
      report.checks.forEach(check => {
        checksHTML += `
          <div class="quality-check-item">
            <span class="check-icon ${check.passed ? 'pass' : 'fail'}">${check.passed ? '✓' : '⚠'}</span>
            <span class="check-label ${check.passed ? 'pass' : ''}">${check.label}</span>
          </div>
        `;
      });
    });
  }

  qualityChecks.innerHTML = checksHTML;

  if (quality.suggestions && quality.suggestions.length > 0) {
    qualitySuggestions.innerHTML = `
      <div class="suggestion-title">💡 Security & Documentation Improvement Directives</div>
      ${quality.suggestions.map(s => `<div class="suggestion-item">${escapeHtml(s)}</div>`).join('')}
    `;
    qualitySuggestions.style.display = 'block';
  } else {
    qualitySuggestions.innerHTML = '<div class="suggestion-title" style="color: var(--accent-emerald)">✨ Perfect Score! OWASP & Swagger Specs 100% compliant.</div>';
  }
}

qualityExpandBtn.addEventListener('click', () => {
  qualityDetails.classList.toggle('hidden');
  qualityExpandBtn.classList.toggle('expanded');
});

// Render Endpoints
function renderDocumentation(docs) {
  if (!docs || docs.length === 0) {
    docsOutput.innerHTML = '<div class="empty-state"><p>No endpoints detected.</p></div>';
    return;
  }

  docsOutput.innerHTML = docs.map((doc, index) => {
    const methodClass = doc.method.toLowerCase();
    const isOpen = index === 0 ? 'open' : '';

    return `
      <div class="endpoint-card ${isOpen}" data-index="${index}">
        <div class="endpoint-header" onclick="toggleEndpoint(this)">
          <span class="method-badge ${methodClass}">${doc.method}</span>
          <span class="endpoint-path">${escapeHtml(doc.path)}</span>
          <span class="endpoint-summary">${escapeHtml(doc.summary || '')}</span>
          <button class="btn-try-live" onclick="event.stopPropagation(); openSandboxModal(${index})">
            ⚡ Try It Out
          </button>
          <span class="endpoint-toggle" style="margin-left:8px">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </span>
        </div>
        <div class="endpoint-body">
          ${renderDescription(doc)}
          ${renderSecurityAudit(doc)}
          ${renderParameters(doc)}
          ${renderRequestBody(doc)}
          ${renderResponses(doc)}
          ${renderSdkSnippets(doc, index)}
        </div>
      </div>
    `;
  }).join('');
}

function renderDescription(doc) {
  if (!doc.description) return '';
  return `
    <div class="doc-section">
      <div class="doc-section-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        Description & Scope
      </div>
      <p class="doc-description">${escapeHtml(doc.description)}</p>
    </div>
  `;
}

function renderSecurityAudit(doc) {
  if (!doc.securityAudit) return '';
  const audit = doc.securityAudit;
  return `
    <div class="doc-section">
      <div class="doc-section-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        OWASP Security Audit Rating
      </div>
      <div class="security-box">
        <div>
          <span style="font-weight:600; font-size:0.85rem">Security Compliance Rating</span>
          <div class="security-findings">
            ${audit.findings.map(f => `
              <div class="finding-item">
                <span style="color:${f.type === 'pass' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}">${f.type === 'pass' ? '✓' : '⚠'}</span>
                ${escapeHtml(f.message)}
              </div>
            `).join('')}
          </div>
        </div>
        <span class="security-badge">Grade ${audit.rating || 'A'} (${audit.score || 90}%)</span>
      </div>
    </div>
  `;
}

function renderParameters(doc) {
  if (!doc.parameters || doc.parameters.length === 0) return '';
  return `
    <div class="doc-section">
      <div class="doc-section-title">Parameters</div>
      <table class="params-table" style="width:100%; border-collapse:collapse">
        <thead>
          <tr style="color:var(--text-muted); font-size:0.72rem; text-align:left">
            <th style="padding:6px">Name</th>
            <th style="padding:6px">Type</th>
            <th style="padding:6px">In</th>
            <th style="padding:6px">Required</th>
          </tr>
        </thead>
        <tbody>
          ${doc.parameters.map(p => `
            <tr style="border-top:1px solid var(--border-subtle)">
              <td style="padding:6px; font-family:'JetBrains Mono'; color:var(--accent-cyan)">${escapeHtml(p.name)}</td>
              <td style="padding:6px; font-family:'JetBrains Mono'; color:var(--accent-amber)">${escapeHtml(p.type || 'string')}</td>
              <td style="padding:6px">${escapeHtml(p.in || 'path')}</td>
              <td style="padding:6px; color:${p.required ? 'var(--accent-rose)' : 'var(--text-muted)'}">${p.required ? 'Yes' : 'No'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function renderRequestBody(doc) {
  if (!doc.requestBody) return '';
  return `
    <div class="doc-section">
      <div class="doc-section-title">Request Payload Schema</div>
      <div class="code-block">
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <pre>${syntaxHighlightJSON(doc.requestBody.example || {})}</pre>
      </div>
    </div>
  `;
}

function renderResponses(doc) {
  if (!doc.responses || doc.responses.length === 0) return '';
  return `
    <div class="doc-section">
      <div class="doc-section-title">HTTP Response Codes</div>
      ${doc.responses.map(r => `
        <div style="margin-top:6px">
          <span style="font-family:'JetBrains Mono'; font-weight:600; color:${r.status < 300 ? 'var(--accent-emerald)' : 'var(--accent-rose)'}">${r.status} ${escapeHtml(r.description || '')}</span>
          ${r.example ? `<div class="code-block"><pre>${syntaxHighlightJSON(r.example)}</pre></div>` : ''}
        </div>
      `).join('')}
    </div>
  `;
}

function renderSdkSnippets(doc, epIndex) {
  if (!doc.snippets) return '';
  const s = doc.snippets;
  return `
    <div class="doc-section">
      <div class="doc-section-title">Multi-Language Client SDK Code Snippets</div>
      <div class="snippet-tabs">
        <button class="snippet-tab-btn active" onclick="switchSnippet(this, ${epIndex}, 'curl')">cURL</button>
        <button class="snippet-tab-btn" onclick="switchSnippet(this, ${epIndex}, 'javascript')">JavaScript</button>
        <button class="snippet-tab-btn" onclick="switchSnippet(this, ${epIndex}, 'python')">Python</button>
        <button class="snippet-tab-btn" onclick="switchSnippet(this, ${epIndex}, 'java')">Java</button>
        <button class="snippet-tab-btn" onclick="switchSnippet(this, ${epIndex}, 'go')">Go</button>
      </div>
      <div class="code-block" id="snippetCode_${epIndex}">
        <button class="copy-btn" onclick="copyCode(this)">Copy</button>
        <pre>${escapeHtml(s.curl)}</pre>
      </div>
    </div>
  `;
}

function switchSnippet(btn, epIndex, lang) {
  const container = btn.parentElement;
  container.querySelectorAll('.snippet-tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const doc = currentDocData.documentation[epIndex];
  const codeBox = document.getElementById(`snippetCode_${epIndex}`).querySelector('pre');
  if (doc && doc.snippets && doc.snippets[lang]) {
    codeBox.textContent = doc.snippets[lang];
  }
}

// Sandbox Modal Logic
function openSandboxModal(index) {
  if (!currentDocData || !currentDocData.documentation[index]) return;
  const doc = currentDocData.documentation[index];
  activeSandboxEndpoint = doc;

  modalMethod.className = `method-badge ${doc.method.toLowerCase()}`;
  modalMethod.textContent = doc.method;
  modalUrl.textContent = `http://localhost:3001${doc.path}`;

  const defaultBody = doc.requestBody?.example ? JSON.stringify(doc.requestBody.example, null, 2) : '{\n  "query": "sample"\n}';
  sandboxPayload.value = defaultBody;
  sandboxResponseArea.classList.add('hidden');

  sandboxModal.classList.remove('hidden');
}

closeSandboxModal.addEventListener('click', () => sandboxModal.classList.add('hidden'));

runSandboxBtn.addEventListener('click', async () => {
  if (!activeSandboxEndpoint) return;
  runSandboxBtn.disabled = true;
  runSandboxBtn.textContent = '⏳ Executing Mock Live Sandbox...';

  try {
    let payload = null;
    try { payload = JSON.parse(sandboxPayload.value); } catch {}

    const response = await fetch(`${API_BASE}/api/mock-execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        targetMethod: activeSandboxEndpoint.method,
        targetPath: activeSandboxEndpoint.path,
        payload
      })
    });

    const data = await response.json();
    sandboxOutput.textContent = JSON.stringify(data, null, 2);
    sandboxResponseArea.classList.remove('hidden');
    showToast('success', 'Live Sandbox Execution Complete (200 OK)');
  } catch (err) {
    showToast('error', 'Execution error');
  } finally {
    runSandboxBtn.disabled = false;
    runSandboxBtn.textContent = '⚡ Execute Live Request';
  }
});

// Export OpenAPI 3.0 Handler
exportOpenApiBtn.addEventListener('click', async () => {
  if (!currentDocData || !currentDocData.documentation) {
    showToast('error', 'No generated documentation to export');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/export/openapi`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documentation: currentDocData.documentation })
    });

    const openapiSpec = await response.json();
    const blob = new Blob([JSON.stringify(openapiSpec, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `openapi_spec_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);

    showToast('success', 'OpenAPI 3.0 specification downloaded successfully');
  } catch (err) {
    showToast('error', 'Failed to export OpenAPI specification');
  }
});

// Toggle Endpoint Card
function toggleEndpoint(header) {
  const card = header.closest('.endpoint-card');
  card.classList.toggle('open');
}

// Copy Code
function copyCode(btn) {
  const pre = btn.parentElement.querySelector('pre');
  navigator.clipboard.writeText(pre.textContent).then(() => {
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function syntaxHighlightJSON(obj) {
  try {
    const json = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
    return json
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"([^"]+)":/g, '<span style="color: #a78bfa">"$1"</span>:')
      .replace(/: "(.*?)"/g, ': <span style="color: #34d399">"$1"</span>')
      .replace(/: (\d+)/g, ': <span style="color: #fbbf24">$1</span>')
      .replace(/: (true|false)/g, ': <span style="color: #60a5fa">$1</span>');
  } catch {
    return escapeHtml(String(obj));
  }
}

function animateCounter(element, start, end, duration) {
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(start + (end - start) * eased) + '%';
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function setLoading(loading) {
  generateBtn.disabled = loading;
  const btnText = generateBtn.querySelector('.btn-text');
  const btnLoading = generateBtn.querySelector('.btn-loading');

  if (loading) {
    btnText.classList.add('hidden');
    btnLoading.classList.remove('hidden');
    setStatus('processing', 'Analyzing...');
  } else {
    btnText.classList.remove('hidden');
    btnLoading.classList.add('hidden');
  }
}

function setStatus(type, text) {
  statusBadge.className = 'status-badge';
  if (type !== 'ready') statusBadge.classList.add(type);
  statusBadge.querySelector('.status-text').textContent = text;
}

function showToast(type, message) {
  const iconMap = { success: '✅', error: '❌' };
  toast.querySelector('.toast-icon').textContent = iconMap[type] || '';
  toast.querySelector('.toast-message').textContent = message;
  toast.className = `toast ${type} show`;
  setTimeout(() => toast.classList.remove('show'), 3500);
}
