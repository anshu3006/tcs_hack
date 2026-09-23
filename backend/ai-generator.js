/**
 * AI Documentation Generator
 * Uses Google Gemini to generate rich API documentation from parsed endpoints.
 */

const { GoogleGenerativeAI } = require('@google/generative-ai');

async function generateDocumentation(code, parsedEndpoints, language) {
  const apiKey = process.env.GEMINI_API_KEY;

  if (!apiKey || apiKey === 'YOUR_GEMINI_API_KEY_HERE') {
    console.log('⚠️  No Gemini API key found. Using fallback documentation generation.');
    return generateFallbackDocs(code, parsedEndpoints);
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

    const prompt = buildPrompt(code, parsedEndpoints, language);

    const result = await model.generateContent(prompt);
    const response = result.response;
    const text = response.text();

    // Parse the AI response into structured format
    const documentation = parseAIResponse(text, parsedEndpoints);
    return documentation;
  } catch (error) {
    console.error('AI generation failed, using fallback:', error.message);
    return generateFallbackDocs(code, parsedEndpoints);
  }
}

function buildPrompt(code, parsedEndpoints, language) {
  const endpointSummary = parsedEndpoints.map(ep =>
    `- ${ep.method} ${ep.path} (function: ${ep.functionName}, framework: ${ep.framework})`
  ).join('\n');

  return `You are an expert API documentation generator. Analyze the following API code and generate comprehensive, clear documentation.

## Source Code
\`\`\`${language || ''}
${code}
\`\`\`

## Detected Endpoints
${endpointSummary}

## Instructions
For EACH endpoint, generate documentation in the following JSON format. Return ONLY a valid JSON array, no markdown code fences:

[
  {
    "method": "GET",
    "path": "/api/users",
    "summary": "A short one-line description",
    "description": "A detailed explanation of what this endpoint does, including business logic",
    "parameters": [
      {
        "name": "param_name",
        "type": "string",
        "required": true,
        "in": "query|path|body|header",
        "description": "What this parameter does"
      }
    ],
    "requestBody": {
      "contentType": "application/json",
      "description": "Description of the request body",
      "schema": {
        "field1": { "type": "string", "description": "..." },
        "field2": { "type": "integer", "description": "..." }
      },
      "example": { "field1": "value1", "field2": 42 }
    },
    "responses": [
      {
        "status": 200,
        "description": "Success response description",
        "example": { "id": 1, "name": "..." }
      },
      {
        "status": 400,
        "description": "Error response description",
        "example": { "error": "..." }
      }
    ],
    "tags": ["users", "authentication"],
    "notes": "Any additional notes or warnings"
  }
]

IMPORTANT:
- Generate realistic example values, not generic placeholders
- Include ALL possible response status codes (200, 201, 400, 404, 500, etc.)
- Identify body parameters from the code even if not in route params
- Be specific about data types
- Include authentication requirements if any are visible in the code
- Return ONLY the JSON array, no other text`;
}

function parseAIResponse(text, parsedEndpoints) {
  try {
    // Try to extract JSON from response
    let jsonStr = text.trim();

    // Remove markdown code fences if present
    jsonStr = jsonStr.replace(/^```(?:json)?\s*\n?/i, '').replace(/\n?```\s*$/i, '');

    const parsed = JSON.parse(jsonStr);

    if (Array.isArray(parsed)) {
      return parsed.map(doc => ({
        method: doc.method || 'GET',
        path: doc.path || '/',
        summary: doc.summary || '',
        description: doc.description || '',
        parameters: doc.parameters || [],
        requestBody: doc.requestBody || null,
        responses: doc.responses || [],
        tags: doc.tags || [],
        notes: doc.notes || '',
        source: 'ai'
      }));
    }

    return generateFallbackDocs('', parsedEndpoints);
  } catch (e) {
    console.error('Failed to parse AI response:', e.message);
    // Try to salvage partial JSON
    try {
      const jsonMatch = text.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]).map(doc => ({
          method: doc.method || 'GET',
          path: doc.path || '/',
          summary: doc.summary || '',
          description: doc.description || '',
          parameters: doc.parameters || [],
          requestBody: doc.requestBody || null,
          responses: doc.responses || [],
          tags: doc.tags || [],
          notes: doc.notes || '',
          source: 'ai'
        }));
      }
    } catch { }

    return generateFallbackDocs('', parsedEndpoints);
  }
}

function generateFallbackDocs(code, parsedEndpoints) {
  return parsedEndpoints.map(ep => {
    const isCreate = ep.method === 'POST';
    const isUpdate = ep.method === 'PUT' || ep.method === 'PATCH';
    const isDelete = ep.method === 'DELETE';
    const isRead = ep.method === 'GET';

    // Extract resource name from path
    const pathParts = ep.path.split('/').filter(Boolean);
    const resource = pathParts.find(p => !p.startsWith(':') && !p.startsWith('{') && p !== 'api' && p !== 'v1' && p !== 'v2') || 'resource';
    const resourceSingular = resource.endsWith('s') ? resource.slice(0, -1) : resource;

    let summary = '';
    let description = '';

    if (isRead && ep.params.length === 0) {
      summary = `List all ${resource}`;
      description = `Retrieves a list of all ${resource}. Results may be paginated.`;
    } else if (isRead) {
      summary = `Get ${resourceSingular} by ID`;
      description = `Retrieves a specific ${resourceSingular} by its unique identifier.`;
    } else if (isCreate) {
      summary = `Create a new ${resourceSingular}`;
      description = `Creates a new ${resourceSingular} with the provided data in the request body.`;
    } else if (isUpdate) {
      summary = `Update ${resourceSingular}`;
      description = `Updates an existing ${resourceSingular} with the provided data.`;
    } else if (isDelete) {
      summary = `Delete ${resourceSingular}`;
      description = `Permanently removes a ${resourceSingular} from the system.`;
    } else {
      summary = `${ep.method} ${ep.path}`;
      description = `Handles ${ep.method} requests to ${ep.path}.`;
    }

    const successStatus = isCreate ? 201 : isDelete ? 204 : 200;
    const successDesc = isCreate ? 'Created' : isDelete ? 'No Content' : 'OK';

    return {
      method: ep.method,
      path: ep.path,
      summary,
      description,
      parameters: ep.params.map(p => ({
        ...p,
        description: `The ${p.name} ${p.in === 'path' ? 'path parameter' : 'parameter'}`
      })),
      requestBody: (isCreate || isUpdate) ? {
        contentType: 'application/json',
        description: `${resourceSingular} data`,
        schema: {},
        example: {}
      } : null,
      responses: [
        {
          status: successStatus,
          description: successDesc,
          example: isDelete ? null : (isRead && ep.params.length === 0) ? [{ id: 1 }] : { id: 1 }
        },
        ...(ep.params.length > 0 ? [{ status: 404, description: `${resourceSingular} not found`, example: { error: `${resourceSingular} not found` } }] : []),
        { status: 500, description: 'Internal Server Error', example: { error: 'Server error' } }
      ],
      tags: [resource],
      notes: `Detected from ${ep.framework} framework.`,
      source: 'fallback'
    };
  });
}

module.exports = { generateDocumentation };
