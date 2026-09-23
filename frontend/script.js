/**
 * DocForge AI — Frontend Application Logic
 */

const API_BASE = window.location.origin;

// --- DOM Elements ---
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
const generatedAt = document.getElementById('generatedAt');
const toast = document.getElementById('toast');

let uploadedFile = null;
let currentTab = 'paste';

// --- Tab Switching ---
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

// --- Line Numbers ---
function updateLineNumbers() {
  const lines = codeInput.value.split('\n').length;
  const nums = [];
  for (let i = 1; i <= Math.max(lines, 20); i++) {
    nums.push(i);
  }
  lineNumbers.textContent = nums.join('\n');
}

codeInput.addEventListener('input', updateLineNumbers);
codeInput.addEventListener('scroll', () => {
  lineNumbers.scrollTop = codeInput.scrollTop;
});
updateLineNumbers();

// --- File Upload ---
uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  if (e.dataTransfer.files.length > 0) {
    handleFile(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    handleFile(fileInput.files[0]);
  }
});

function handleFile(file) {
  uploadedFile = file;
  fileName.textContent = file.name;
  fileInfo.classList.remove('hidden');
  uploadZone.style.display = 'none';

  // Auto-detect language from extension
  const ext = file.name.split('.').pop().toLowerCase();
  const langMap = { py: 'python', js: 'javascript', ts: 'typescript', java: 'java', go: 'go', json: 'json', yaml: 'yaml', yml: 'yaml' };
  if (langMap[ext]) {
    languageSelect.value = langMap[ext];
  }

  showToast('success', `File loaded: ${file.name}`);
}

removeFileBtn.addEventListener('click', () => {
  uploadedFile = null;
  fileInput.value = '';
  fileInfo.classList.add('hidden');
  uploadZone.style.display = 'flex';
});

// --- Sample Code ---
document.querySelectorAll('.sample-card').forEach(card => {
  card.addEventListener('click', () => {
    const sampleKey = card.dataset.sample;
    const sample = SAMPLES[sampleKey];
    if (sample) {
      codeInput.value = sample.code;
      languageSelect.value = sample.language;
      updateLineNumbers();

      // Switch to paste tab
      document.querySelector('[data-tab="paste"]').click();

      showToast('success', `Loaded ${sample.name} sample`);
    }
  });
});

// --- Generate Documentation ---
generateBtn.addEventListener('click', handleGenerate);

// Ctrl+Enter shortcut
codeInput.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    handleGenerate();
  }

  // Tab key support in editor
  if (e.key === 'Tab') {
    e.preventDefault();
    const start = codeInput.selectionStart;
    const end = codeInput.selectionEnd;
    codeInput.value = codeInput.value.substring(0, start) + '  ' + codeInput.value.substring(end);
    codeInput.selectionStart = codeInput.selectionEnd = start + 2;
    updateLineNumbers();
  }
});

async function handleGenerate() {
  // Determine if using file or pasted code
  if (currentTab === 'upload' && uploadedFile) {
    await generateFromFile();
  } else {
    await generateFromCode();
  }
}

async function generateFromCode() {
  const code = codeInput.value.trim();
  if (!code) {
    showToast('error', 'Please paste some API code first');
    codeInput.focus();
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        language: languageSelect.value,
        format: 'json'
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || data.error || 'Generation failed');
    }

    renderResults(data);
    showToast('success', `Generated docs for ${data.metadata.endpointCount} endpoints`);
  } catch (err) {
    console.error('Generation error:', err);
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

    if (!response.ok) {
      throw new Error(data.message || data.error || 'Upload failed');
    }

    renderResults(data);
    showToast('success', `Generated docs for ${data.metadata.endpointCount} endpoints`);
  } catch (err) {
    console.error('Upload error:', err);
    showToast('error', err.message || 'Failed to process file');
    setStatus('error', 'Error');
  } finally {
    setLoading(false);
  }
}

// --- Render Results ---
function renderResults(data) {
  emptyState.classList.add('hidden');
  results.classList.remove('hidden');

  // Render quality
  renderQuality(data.quality);

  // Render metadata
  endpointCount.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
    ${data.metadata.endpointCount} endpoint${data.metadata.endpointCount !== 1 ? 's' : ''}
  `;

  const time = new Date(data.metadata.generatedAt);
  generatedAt.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
    ${time.toLocaleTimeString()}
  `;

  // Render documentation cards
  renderDocumentation(data.documentation);

  setStatus('ready', 'Complete');
}

function renderQuality(quality) {
  // Animate score ring
  const circumference = 2 * Math.PI * 34; // r=34
  const offset = circumference - (quality.score / 100) * circumference;

  // Reset and animate
  qualityRingCircle.style.transition = 'none';
  qualityRingCircle.setAttribute('stroke-dashoffset', circumference);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      qualityRingCircle.style.transition = 'stroke-dashoffset 1.5s ease-out';
      qualityRingCircle.setAttribute('stroke-dashoffset', offset);
    });
  });

  // Animate score counter
  animateCounter(qualityScore, 0, quality.score, 1200);

  qualityGrade.textContent = quality.grade;
  qualitySummary.textContent = quality.summary;

  // Color the grade based on score
  if (quality.score >= 80) {
    qualityGrade.style.background = 'linear-gradient(135deg, #34d399, #059669)';
  } else if (quality.score >= 60) {
    qualityGrade.style.background = 'linear-gradient(135deg, #fbbf24, #d97706)';
  } else {
    qualityGrade.style.background = 'linear-gradient(135deg, #fb7185, #e11d48)';
  }

  // Render quality checks
  renderQualityChecks(quality);
}

function renderQualityChecks(quality) {
  let checksHTML = '';

  // Flatten all checks from endpoint reports
  if (quality.endpointReports && quality.endpointReports.length > 0) {
    quality.endpointReports.forEach(report => {
      report.checks.forEach(check => {
        checksHTML += `
          <div class="quality-check-item">
            <span class="check-icon ${check.passed ? 'pass' : 'fail'}">
              ${check.passed ? '✓' : '⚠'}
            </span>
            <span class="check-label ${check.passed ? 'pass' : ''}">${check.label}</span>
          </div>
        `;
      });
    });
  }

  // Global checks
  if (quality.globalChecks) {
    quality.globalChecks.forEach(check => {
      checksHTML += `
        <div class="quality-check-item">
          <span class="check-icon ${check.passed ? 'pass' : 'fail'}">
            ${check.passed ? '✓' : '⚠'}
          </span>
          <span class="check-label ${check.passed ? 'pass' : ''}">${check.label}</span>
        </div>
      `;
    });
  }

  qualityChecks.innerHTML = checksHTML;

  // Suggestions
  if (quality.suggestions && quality.suggestions.length > 0) {
    qualitySuggestions.innerHTML = `
      <div class="suggestion-title">💡 Suggestions for Improvement</div>
      ${quality.suggestions.map(s => `<div class="suggestion-item">${escapeHtml(s)}</div>`).join('')}
    `;
    qualitySuggestions.style.display = 'block';
  } else {
    qualitySuggestions.innerHTML = '<div class="suggestion-title" style="color: var(--accent-emerald)">✨ No suggestions — documentation looks great!</div>';
  }
}

// Toggle quality details
qualityExpandBtn.addEventListener('click', () => {
  qualityDetails.classList.toggle('hidden');
  qualityExpandBtn.classList.toggle('expanded');
});

function renderDocumentation(docs) {
  if (!docs || docs.length === 0) {
    docsOutput.innerHTML = '<div class="empty-state"><p>No endpoints found in the code.</p></div>';
    return;
  }

  docsOutput.innerHTML = docs.map((doc, index) => {
    const methodClass = doc.method.toLowerCase();
    const isOpen = index === 0 ? 'open' : '';

    return `
      <div class="endpoint-card ${isOpen}" style="animation-delay: ${index * 80}ms" data-index="${index}">
        <div class="endpoint-header" onclick="toggleEndpoint(this)">
          <span class="method-badge ${methodClass}">${doc.method}</span>
          <span class="endpoint-path">${escapeHtml(doc.path)}</span>
          <span class="endpoint-summary">${escapeHtml(doc.summary || '')}</span>
          <span class="endpoint-toggle">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </span>
        </div>
        <div class="endpoint-body">
          ${renderDescription(doc)}
          ${renderParameters(doc)}
          ${renderRequestBody(doc)}
          ${renderResponses(doc)}
          ${renderTags(doc)}
          ${renderNotes(doc)}
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
        Description
      </div>
      <p class="doc-description">${escapeHtml(doc.description)}</p>
    </div>
  `;
}

function renderParameters(doc) {
  if (!doc.parameters || doc.parameters.length === 0) return '';
  return `
    <div class="doc-section">
      <div class="doc-section-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/></svg>
        Parameters
      </div>
      <table class="params-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>In</th>
            <th>Required</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          ${doc.parameters.map(p => `
            <tr>
              <td><span class="param-name">${escapeHtml(p.name)}</span></td>
              <td><span class="param-type">${escapeHtml(p.type || 'any')}</span></td>
              <td><span class="param-in">${escapeHtml(p.in || '-')}</span></td>
              <td><span class="param-required ${p.required ? 'required' : 'optional'}">${p.required ? 'required' : 'optional'}</span></td>
              <td>${escapeHtml(p.description || '—')}</td>
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
      <div class="doc-section-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        Request Body
        ${doc.requestBody.contentType ? `<span style="font-weight:400; color: var(--text-muted)">(${doc.requestBody.contentType})</span>` : ''}
      </div>
      ${doc.requestBody.description ? `<p class="doc-description" style="margin-bottom:8px">${escapeHtml(doc.requestBody.description)}</p>` : ''}
      ${doc.requestBody.example && Object.keys(doc.requestBody.example).length > 0 ? `
        <div class="code-block">
          <span class="code-block-label">JSON</span>
          <button class="copy-btn" onclick="copyCode(this)">Copy</button>
          <pre>${syntaxHighlightJSON(doc.requestBody.example)}</pre>
        </div>
      ` : ''}
    </div>
  `;
}

function renderResponses(doc) {
  if (!doc.responses || doc.responses.length === 0) return '';
  return `
    <div class="doc-section">
      <div class="doc-section-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
        Responses
      </div>
      ${doc.responses.map(r => {
        const statusClass = r.status < 300 ? 'success' : r.status < 500 ? 'warning' : 'error';
        return `
          <div class="response-group">
            <div class="response-status ${statusClass}">
              <span>${r.status}</span>
              <span style="font-weight:400; color: var(--text-secondary)">${escapeHtml(r.description || '')}</span>
            </div>
            ${r.example !== null && r.example !== undefined ? `
              <div class="code-block">
                <span class="code-block-label">JSON</span>
                <button class="copy-btn" onclick="copyCode(this)">Copy</button>
                <pre>${syntaxHighlightJSON(r.example)}</pre>
              </div>
            ` : ''}
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function renderTags(doc) {
  if (!doc.tags || doc.tags.length === 0) return '';
  return `
    <div class="tags-row">
      ${doc.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join('')}
    </div>
  `;
}

function renderNotes(doc) {
  if (!doc.notes) return '';
  return `<div class="doc-note">📌 ${escapeHtml(doc.notes)}</div>`;
}

// --- Toggle Endpoint ---
function toggleEndpoint(header) {
  const card = header.closest('.endpoint-card');
  card.classList.toggle('open');
}

// --- Copy Code ---
function copyCode(btn) {
  const pre = btn.parentElement.querySelector('pre');
  navigator.clipboard.writeText(pre.textContent).then(() => {
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  });
}

// --- Helpers ---
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function syntaxHighlightJSON(obj) {
  try {
    const json = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
    return json
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"([^"]+)":/g, '<span style="color: #a78bfa">"$1"</span>:')
      .replace(/: "(.*?)"/g, ': <span style="color: #34d399">"$1"</span>')
      .replace(/: (\d+)/g, ': <span style="color: #fbbf24">$1</span>')
      .replace(/: (true|false)/g, ': <span style="color: #60a5fa">$1</span>')
      .replace(/: (null)/g, ': <span style="color: #fb7185">$1</span>');
  } catch {
    return escapeHtml(String(obj));
  }
}

function animateCounter(element, start, end, duration) {
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (end - start) * eased);
    element.textContent = current + '%';
    if (progress < 1) {
      requestAnimationFrame(update);
    }
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
    setStatus('processing', 'Generating...');
  } else {
    btnText.classList.remove('hidden');
    btnLoading.classList.add('hidden');
  }
}

function setStatus(type, text) {
  statusBadge.className = 'status-badge';
  if (type !== 'ready') {
    statusBadge.classList.add(type);
  }
  statusBadge.querySelector('.status-text').textContent = text;
}

function showToast(type, message) {
  const iconMap = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.querySelector('.toast-icon').textContent = iconMap[type] || '';
  toast.querySelector('.toast-message').textContent = message;
  toast.className = `toast ${type} show`;

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}
