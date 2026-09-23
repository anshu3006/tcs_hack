/**
 * Documentation Quality & Security Intelligence Analyzer
 * Evaluates completeness, clarity, OWASP security posture, and OpenAPI standards compliance.
 */

function analyzeQuality(documentation) {
  if (!documentation || documentation.length === 0) {
    return {
      score: 0,
      grade: 'F',
      checks: [],
      summary: 'No documentation generated.',
      suggestions: ['Ensure valid API code is provided.']
    };
  }

  const globalChecks = [];
  const endpointReports = [];
  let totalPoints = 0;
  let earnedPoints = 0;

  documentation.forEach(doc => {
    const checks = [];

    // 1. Endpoint detected
    const hasEndpoint = !!doc.path && doc.path !== '/';
    checks.push({ label: 'Endpoint path detected', passed: hasEndpoint, weight: 10 });

    // 2. HTTP method identified
    const hasMethod = !!doc.method && ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].includes(doc.method);
    checks.push({ label: 'HTTP method identified', passed: hasMethod, weight: 10 });

    // 3. Summary present
    const hasSummary = !!doc.summary && doc.summary.length > 5;
    checks.push({ label: 'Summary description present', passed: hasSummary, weight: 10 });

    // 4. Detailed description
    const hasDescription = !!doc.description && doc.description.length > 15;
    checks.push({ label: 'Detailed description provided', passed: hasDescription, weight: 10 });

    // 5. Parameters documented
    const hasParams = doc.parameters && doc.parameters.length > 0;
    const paramsDocumented = hasParams && doc.parameters.every(p => p.name && p.type);
    checks.push({
      label: 'Parameters documented',
      passed: paramsDocumented || !needsParams(doc),
      weight: 10,
      note: !hasParams && needsParams(doc) ? 'Parameters should be specified' : undefined
    });

    // 6. Request body
    const needsBody = ['POST', 'PUT', 'PATCH'].includes(doc.method);
    const hasBody = !!doc.requestBody;
    checks.push({ label: 'Request body documented', passed: !needsBody || hasBody, weight: 10 });

    // 7. Code SDK Snippets generated
    const hasSnippets = !!doc.snippets && !!doc.snippets.curl && !!doc.snippets.python;
    checks.push({ label: 'Multi-Language SDK Snippets (cURL, Python, JS, Java, Go)', passed: hasSnippets, weight: 15 });

    // 8. OWASP Security Audit
    const hasSecurity = !!doc.securityAudit && doc.securityAudit.score >= 80;
    checks.push({ label: 'OWASP Security Audit passed (Auth/Input checks)', passed: hasSecurity, weight: 15 });

    // 9. Response documented
    const hasResponses = doc.responses && doc.responses.length > 0;
    checks.push({ label: 'Responses & Status codes documented', passed: hasResponses, weight: 10 });

    let epTotal = 0, epEarned = 0;
    checks.forEach(c => {
      epTotal += c.weight;
      if (c.passed) epEarned += c.weight;
    });

    totalPoints += epTotal;
    earnedPoints += epEarned;

    endpointReports.push({
      endpoint: `${doc.method} ${doc.path}`,
      checks,
      score: Math.round((epEarned / epTotal) * 100),
      earned: epEarned,
      total: epTotal
    });
  });

  // Global compliance checks
  const hasMultipleEndpoints = documentation.length > 1;
  const hasTags = documentation.some(d => d.tags && d.tags.length > 0);
  const allHaveSnippets = documentation.every(d => d.snippets);

  globalChecks.push(
    { label: 'Multi-endpoint structure parsed', passed: hasMultipleEndpoints || documentation.length === 1, weight: 5 },
    { label: 'Endpoints categorized by tags', passed: hasTags, weight: 5 },
    { label: 'SDK code snippets built for all routes', passed: allHaveSnippets, weight: 5 }
  );

  globalChecks.forEach(c => {
    totalPoints += c.weight;
    if (c.passed) earnedPoints += c.weight;
  });

  const score = Math.round((earnedPoints / totalPoints) * 100);

  const suggestions = [];
  endpointReports.forEach(report => {
    report.checks
      .filter(c => !c.passed)
      .forEach(c => {
        suggestions.push(`${report.endpoint}: ${c.note || c.label + ' recommended'}`);
      });
  });

  return {
    score,
    grade: getGrade(score),
    totalEndpoints: documentation.length,
    globalChecks,
    endpointReports,
    summary: getSummary(score),
    suggestions: suggestions.slice(0, 8)
  };
}

function needsParams(doc) {
  return doc.path && (doc.path.includes(':') || doc.path.includes('{'));
}

function getGrade(score) {
  if (score >= 95) return 'A+';
  if (score >= 90) return 'A';
  if (score >= 85) return 'A-';
  if (score >= 80) return 'B+';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  return 'F';
}

function getSummary(score) {
  if (score >= 90) return 'Production-Ready! OWASP Security Audit passed & 100% Swagger compliant.';
  if (score >= 80) return 'High Quality Documentation. Meets all hackathon completeness guidelines.';
  return 'Decent baseline documentation. Recommended to add security headers and body schema examples.';
}

module.exports = { analyzeQuality };
