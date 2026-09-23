const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const { parseAPICode } = require('./parser');
const { generateDocumentation } = require('./ai-generator');
const { analyzeQuality } = require('./quality-checker');

// Load env
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;
const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Serve frontend static files
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Main endpoint: Generate documentation from pasted code
app.post('/api/generate', async (req, res) => {
  try {
    const { code, language, format } = req.body;

    if (!code || code.trim().length === 0) {
      return res.status(400).json({ error: 'No code provided' });
    }

    console.log(`\n📄 Received code (${code.length} chars), language: ${language || 'auto-detect'}`);

    // Step 1: Parse the code to extract endpoints
    const parsedEndpoints = parseAPICode(code, language);
    console.log(`🔍 Parsed ${parsedEndpoints.length} endpoints`);

    // Step 2: Use AI to generate rich documentation
    const documentation = await generateDocumentation(code, parsedEndpoints, language);
    console.log(`✨ AI documentation generated`);

    // Step 3: Analyze documentation quality
    const quality = analyzeQuality(documentation);
    console.log(`📊 Quality score: ${quality.score}%`);

    res.json({
      success: true,
      parsedEndpoints,
      documentation,
      quality,
      metadata: {
        language: language || 'auto-detected',
        endpointCount: parsedEndpoints.length,
        generatedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Generation error:', error);
    res.status(500).json({
      error: 'Failed to generate documentation',
      message: error.message
    });
  }
});

// Upload file endpoint
app.post('/api/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const code = req.file.buffer.toString('utf-8');
    const filename = req.file.originalname;
    const ext = path.extname(filename).toLowerCase();

    // Detect language from extension
    const langMap = {
      '.py': 'python',
      '.js': 'javascript',
      '.ts': 'typescript',
      '.java': 'java',
      '.go': 'go',
      '.rb': 'ruby',
      '.php': 'php',
      '.json': 'json',
      '.yaml': 'yaml',
      '.yml': 'yaml'
    };
    const language = langMap[ext] || 'auto';

    console.log(`\n📁 File uploaded: ${filename} (${code.length} chars)`);

    const parsedEndpoints = parseAPICode(code, language);
    console.log(`🔍 Parsed ${parsedEndpoints.length} endpoints`);

    const documentation = await generateDocumentation(code, parsedEndpoints, language);
    console.log(`✨ AI documentation generated`);

    const quality = analyzeQuality(documentation);
    console.log(`📊 Quality score: ${quality.score}%`);

    res.json({
      success: true,
      parsedEndpoints,
      documentation,
      quality,
      metadata: {
        filename,
        language,
        endpointCount: parsedEndpoints.length,
        generatedAt: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('❌ Upload error:', error);
    res.status(500).json({
      error: 'Failed to process uploaded file',
      message: error.message
    });
  }
});

// Catch-all: serve frontend
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`\n🚀 API Doc Generator running at http://localhost:${PORT}`);
  console.log(`📝 Gemini API: ${process.env.GEMINI_API_KEY ? '✅ Configured' : '⚠️  Not configured (set GEMINI_API_KEY)'}`);
});
