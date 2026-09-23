/**
 * API Code Parser
 * Extracts endpoints, HTTP methods, parameters, and route info from various frameworks.
 */

// --- Python / Flask / FastAPI ---
const PYTHON_PATTERNS = [
  // Flask: @app.route('/path', methods=['GET', 'POST'])
  {
    regex: /@app\.route\(\s*['"]([^'"]+)['"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?\s*\)\s*\n\s*def\s+(\w+)\s*\(([^)]*)\)/g,
    extract: (match) => {
      const methods = match[2]
        ? match[2].replace(/['"]/g, '').split(',').map(m => m.trim())
        : ['GET'];
      return methods.map(method => ({
        method: method.toUpperCase(),
        path: match[1],
        functionName: match[3],
        params: extractPythonParams(match[4]),
        framework: 'Flask'
      }));
    }
  },
  // Flask blueprints: @bp.route, @blueprint.route
  {
    regex: /@\w+\.route\(\s*['"]([^'"]+)['"]\s*(?:,\s*methods\s*=\s*\[([^\]]+)\])?\s*\)\s*\n\s*def\s+(\w+)\s*\(([^)]*)\)/g,
    extract: (match) => {
      const methods = match[2]
        ? match[2].replace(/['"]/g, '').split(',').map(m => m.trim())
        : ['GET'];
      return methods.map(method => ({
        method: method.toUpperCase(),
        path: match[1],
        functionName: match[3],
        params: extractPythonParams(match[4]),
        framework: 'Flask'
      }));
    }
  },
  // FastAPI: @app.get('/path'), @app.post('/path'), @router.get, etc.
  {
    regex: /@(?:app|router)\.(get|post|put|delete|patch)\(\s*['"]([^'"]+)['"]\s*(?:,\s*[^)]+)?\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)/g,
    extract: (match) => [{
      method: match[1].toUpperCase(),
      path: match[2],
      functionName: match[3],
      params: extractPythonParams(match[4]),
      framework: 'FastAPI'
    }]
  },
  // Django REST Framework: class-based views
  {
    regex: /class\s+(\w+)\([\w.,\s]*(?:APIView|ViewSet|ModelViewSet)[\w.,\s]*\):\s*\n(?:[\s\S]*?def\s+(get|post|put|delete|patch|list|create|retrieve|update|destroy)\s*\(([^)]*)\))/g,
    extract: (match) => {
      const methodMap = {
        get: 'GET', post: 'POST', put: 'PUT', delete: 'DELETE', patch: 'PATCH',
        list: 'GET', create: 'POST', retrieve: 'GET', update: 'PUT', destroy: 'DELETE'
      };
      return [{
        method: methodMap[match[2]] || 'GET',
        path: `/${match[1].toLowerCase().replace(/viewset|view|api/gi, '')}`,
        functionName: `${match[1]}.${match[2]}`,
        params: extractPythonParams(match[3]),
        framework: 'Django REST'
      }];
    }
  }
];

// --- JavaScript / Express / Koa / Hapi ---
const JS_PATTERNS = [
  // Express: app.get('/path', ...), router.post('/path', ...)
  {
    regex: /(?:app|router)\.(get|post|put|delete|patch|options|head)\(\s*['"`]([^'"`]+)['"`]\s*,/g,
    extract: (match) => [{
      method: match[1].toUpperCase(),
      path: match[2],
      functionName: '',
      params: extractRouteParams(match[2]),
      framework: 'Express'
    }]
  },
  // Express Router style
  {
    regex: /router\.(get|post|put|delete|patch)\(\s*['"`]([^'"`]+)['"`]/g,
    extract: (match) => [{
      method: match[1].toUpperCase(),
      path: match[2],
      functionName: '',
      params: extractRouteParams(match[2]),
      framework: 'Express'
    }]
  },
  // Next.js/Vercel API routes: export async function GET/POST etc.
  {
    regex: /export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)\s*\(/g,
    extract: (match) => [{
      method: match[1].toUpperCase(),
      path: '/api/[from-filename]',
      functionName: match[1],
      params: [],
      framework: 'Next.js API'
    }]
  }
];

// --- Java / Spring Boot ---
const JAVA_PATTERNS = [
  {
    regex: /@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\(\s*(?:value\s*=\s*)?["']([^"']+)["']\s*(?:,\s*method\s*=\s*RequestMethod\.(\w+))?\s*\)\s*\n\s*(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(([^)]*)\)/g,
    extract: (match) => {
      const mappingToMethod = {
        GetMapping: 'GET', PostMapping: 'POST', PutMapping: 'PUT',
        DeleteMapping: 'DELETE', PatchMapping: 'PATCH'
      };
      return [{
        method: mappingToMethod[match[1]] || match[3] || 'GET',
        path: match[2],
        functionName: match[4],
        params: extractJavaParams(match[5]),
        framework: 'Spring Boot'
      }];
    }
  }
];

// --- Go / Gin / Echo / Chi ---
const GO_PATTERNS = [
  {
    regex: /(?:r|router|g|group|e|engine)\.(GET|POST|PUT|DELETE|PATCH)\(\s*["']([^"']+)["']\s*,\s*(\w+)/g,
    extract: (match) => [{
      method: match[1].toUpperCase(),
      path: match[2],
      functionName: match[3],
      params: extractRouteParams(match[2]),
      framework: 'Go (Gin/Echo)'
    }]
  },
  // http.HandleFunc
  {
    regex: /http\.HandleFunc\(\s*["']([^"']+)["']\s*,\s*(\w+)/g,
    extract: (match) => [{
      method: 'ANY',
      path: match[1],
      functionName: match[2],
      params: [],
      framework: 'Go net/http'
    }]
  }
];

// --- JSON / OpenAPI / Swagger definitions ---
function parseJSONDefinition(code) {
  try {
    const parsed = JSON.parse(code);

    // OpenAPI/Swagger format
    if (parsed.paths) {
      const endpoints = [];
      for (const [path, methods] of Object.entries(parsed.paths)) {
        for (const [method, details] of Object.entries(methods)) {
          if (['get', 'post', 'put', 'delete', 'patch', 'options', 'head'].includes(method)) {
            const params = [];
            if (details.parameters) {
              details.parameters.forEach(p => {
                params.push({
                  name: p.name,
                  type: p.schema?.type || p.type || 'string',
                  required: p.required || false,
                  in: p.in || 'query',
                  description: p.description || ''
                });
              });
            }
            endpoints.push({
              method: method.toUpperCase(),
              path,
              functionName: details.operationId || details.summary || '',
              params,
              framework: 'OpenAPI',
              summary: details.summary || '',
              description: details.description || '',
              requestBody: details.requestBody || null,
              responses: details.responses || {}
            });
          }
        }
      }
      return endpoints;
    }

    // Simple JSON format: { "endpoints": [...] }
    if (parsed.endpoints && Array.isArray(parsed.endpoints)) {
      return parsed.endpoints.map(ep => ({
        method: (ep.method || 'GET').toUpperCase(),
        path: ep.path || ep.url || ep.route || '/',
        functionName: ep.name || ep.handler || '',
        params: (ep.params || ep.parameters || []).map(p => ({
          name: p.name,
          type: p.type || 'string',
          required: p.required !== false,
          in: p.in || 'body'
        })),
        framework: 'JSON Definition'
      }));
    }

    return [];
  } catch {
    return [];
  }
}

// --- YAML parsing (basic) ---
function parseYAMLDefinition(code) {
  // Basic YAML path extraction for OpenAPI
  const endpoints = [];
  const pathRegex = /^  (\/[^\s:]+):\s*$/gm;
  const methodRegex = /^\s{4}(get|post|put|delete|patch):\s*$/gm;

  let currentPath = null;
  const lines = code.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const pathMatch = line.match(/^  (\/[^\s:]+):\s*$/);
    if (pathMatch) {
      currentPath = pathMatch[1];
      continue;
    }
    const methodMatch = line.match(/^\s{4}(get|post|put|delete|patch):\s*$/);
    if (methodMatch && currentPath) {
      // Look ahead for summary
      let summary = '';
      for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
        const sumMatch = lines[j].match(/^\s+summary:\s*(.+)$/);
        if (sumMatch) {
          summary = sumMatch[1].replace(/^['"]|['"]$/g, '');
          break;
        }
      }
      endpoints.push({
        method: methodMatch[1].toUpperCase(),
        path: currentPath,
        functionName: summary,
        params: [],
        framework: 'OpenAPI YAML'
      });
    }
  }

  return endpoints;
}

// --- Helpers ---
function extractPythonParams(paramStr) {
  if (!paramStr) return [];
  return paramStr.split(',')
    .map(p => p.trim())
    .filter(p => p && p !== 'self' && p !== 'request' && p !== 'db')
    .map(p => {
      const parts = p.split(':');
      const nameDefault = parts[0].trim().split('=');
      return {
        name: nameDefault[0].trim(),
        type: parts[1] ? parts[1].trim().split('=')[0].trim() : 'any',
        required: !p.includes('='),
        in: 'path'
      };
    });
}

function extractRouteParams(path) {
  const params = [];
  const matches = path.matchAll(/:(\w+)/g);
  for (const m of matches) {
    params.push({ name: m[1], type: 'string', required: true, in: 'path' });
  }
  // Also handle {param} style
  const bracketMatches = path.matchAll(/\{(\w+)\}/g);
  for (const m of bracketMatches) {
    params.push({ name: m[1], type: 'string', required: true, in: 'path' });
  }
  return params;
}

function extractJavaParams(paramStr) {
  if (!paramStr) return [];
  const params = [];
  const regex = /@(PathVariable|RequestParam|RequestBody)\s*(?:\([^)]*\))?\s*(\w+)\s+(\w+)/g;
  let match;
  while ((match = regex.exec(paramStr)) !== null) {
    params.push({
      name: match[3],
      type: match[2],
      required: true,
      in: match[1] === 'PathVariable' ? 'path' : match[1] === 'RequestBody' ? 'body' : 'query'
    });
  }
  return params;
}

function detectLanguage(code) {
  if (code.includes('@app.route') || code.includes('@app.get') || code.includes('@router.')) return 'python';
  if (code.includes('app.get(') || code.includes('router.get(') || code.includes('express()')) return 'javascript';
  if (code.includes('@GetMapping') || code.includes('@PostMapping') || code.includes('@RestController')) return 'java';
  if (code.includes('func ') && (code.includes('.GET(') || code.includes('HandleFunc'))) return 'go';
  if (code.trim().startsWith('{')) return 'json';
  if (code.includes('openapi:') || code.includes('swagger:') || code.includes('paths:')) return 'yaml';
  return 'unknown';
}

function parseAPICode(code, language) {
  // Auto-detect language if not specified
  const lang = language && language !== 'auto' ? language : detectLanguage(code);

  let allEndpoints = [];

  // Try JSON/YAML first
  if (lang === 'json') return parseJSONDefinition(code);
  if (lang === 'yaml') return parseYAMLDefinition(code);

  // Select patterns based on language
  let patterns = [];
  switch (lang) {
    case 'python':
      patterns = PYTHON_PATTERNS;
      break;
    case 'javascript':
    case 'typescript':
      patterns = JS_PATTERNS;
      break;
    case 'java':
      patterns = JAVA_PATTERNS;
      break;
    case 'go':
      patterns = GO_PATTERNS;
      break;
    default:
      // Try all patterns
      patterns = [...PYTHON_PATTERNS, ...JS_PATTERNS, ...JAVA_PATTERNS, ...GO_PATTERNS];
  }

  for (const pattern of patterns) {
    const regex = new RegExp(pattern.regex.source, pattern.regex.flags);
    let match;
    while ((match = regex.exec(code)) !== null) {
      const extracted = pattern.extract(match);
      allEndpoints.push(...extracted);
    }
  }

  // Deduplicate
  const seen = new Set();
  allEndpoints = allEndpoints.filter(ep => {
    const key = `${ep.method}:${ep.path}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return allEndpoints;
}

module.exports = { parseAPICode, detectLanguage };
