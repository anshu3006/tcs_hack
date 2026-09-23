/**
 * Documentation Quality Checker
 * Analyzes generated documentation for completeness and clarity.
 * This is the "personal touch" feature.
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

  // Per-endpoint quality checks
  documentation.forEach(doc => {
    const checks = [];

    // 1. Endpoint detected
    const hasEndpoint = !!doc.path && doc.path !== '/';
    checks.push({
      label: 'Endpoint path detected',
      passed: hasEndpoint,
      weight: 10
    });

    // 2. HTTP method identified
    const hasMethod = !!doc.method && ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'].includes(doc.method);
    checks.push({
      label: 'HTTP method identified',
      passed: hasMethod,
      weight: 10
    });

    // 3. Summary present
    const hasSummary = !!doc.summary && doc.summary.length > 5;
    checks.push({
      label: 'Summary description present',
      passed: hasSummary,
      weight: 15
    });

    // 4. Detailed description
    const hasDescription = !!doc.description && doc.description.length > 20;
    checks.push({
      label: 'Detailed description provided',
      passed: hasDescription,
      weight: 10
    });

    // 5. Parameters documented
    const hasParams = doc.parameters && doc.parameters.length > 0;
    const paramsDocumented = hasParams && doc.parameters.every(p => p.name && p.type);
    checks.push({
      label: 'Parameters documented',
      passed: paramsDocumented || !needsParams(doc),
      weight: 15,
      note: !hasParams && needsParams(doc) ? 'Parameters may be missing' : undefined
    });

    // 6. Request body (for POST/PUT/PATCH)
    const needsBody = ['POST', 'PUT', 'PATCH'].includes(doc.method);
    const hasBody = !!doc.requestBody;
    checks.push({
      label: 'Request body documented',
      passed: !needsBody || hasBody,
      weight: 10,
      note: needsBody && !hasBody ? 'POST/PUT/PATCH should include request body' : undefined
    });

    // 7. Request example available
    const hasRequestExample = hasBody && doc.requestBody.example && Object.keys(doc.requestBody.example).length > 0;
    checks.push({
      label: 'Request example available',
      passed: !needsBody || hasRequestExample,
      weight: 10,
      note: needsBody && !hasRequestExample ? 'Request example recommended' : undefined
    });

    // 8. Response documented
    const hasResponses = doc.responses && doc.responses.length > 0;
    checks.push({
      label: 'Response documented',
      passed: hasResponses,
      weight: 10
    });

    // 9. Success response example
    const hasSuccessExample = hasResponses && doc.responses.some(r =>
      r.status >= 200 && r.status < 300 && r.example !== null && r.example !== undefined
    );
    checks.push({
      label: 'Success response example',
      passed: hasSuccessExample,
      weight: 5
    });

    // 10. Error response documented
    const hasErrorResponse = hasResponses && doc.responses.some(r => r.status >= 400);
    checks.push({
      label: 'Error response documented',
      passed: hasErrorResponse,
      weight: 5
    });

    // Calculate per-endpoint score
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

  // Global checks
  const hasMultipleEndpoints = documentation.length > 1;
  const hasTags = documentation.some(d => d.tags && d.tags.length > 0);
  const allHaveDescriptions = documentation.every(d => d.description && d.description.length > 10);

  globalChecks.push(
    { label: 'Multiple endpoints documented', passed: hasMultipleEndpoints || documentation.length === 1, weight: 5 },
    { label: 'Endpoints tagged/categorized', passed: hasTags, weight: 5 },
    { label: 'All endpoints have descriptions', passed: allHaveDescriptions, weight: 5 }
  );

  globalChecks.forEach(c => {
    totalPoints += c.weight;
    if (c.passed) earnedPoints += c.weight;
  });

  const score = Math.round((earnedPoints / totalPoints) * 100);

  // Generate suggestions
  const suggestions = [];
  endpointReports.forEach(report => {
    report.checks
      .filter(c => !c.passed)
      .forEach(c => {
        suggestions.push(`${report.endpoint}: ${c.note || c.label + ' is missing'}`);
      });
  });
  globalChecks.filter(c => !c.passed).forEach(c => {
    suggestions.push(c.label);
  });

  return {
    score,
    grade: getGrade(score),
    totalEndpoints: documentation.length,
    globalChecks,
    endpointReports,
    summary: getSummary(score),
    suggestions: suggestions.slice(0, 10) // Top 10 suggestions
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
  if (score >= 75) return 'B';
  if (score >= 70) return 'B-';
  if (score >= 65) return 'C+';
  if (score >= 60) return 'C';
  if (score >= 50) return 'D';
  return 'F';
}

function getSummary(score) {
  if (score >= 90) return 'Excellent documentation! Comprehensive and clear.';
  if (score >= 80) return 'Good documentation. Minor improvements suggested.';
  if (score >= 70) return 'Decent documentation. Some areas need attention.';
  if (score >= 60) return 'Below average. Several important elements are missing.';
  return 'Needs significant improvement. Key documentation elements are missing.';
}

module.exports = { analyzeQuality };
