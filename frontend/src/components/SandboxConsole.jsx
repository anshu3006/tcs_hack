import { useState, useEffect } from 'react';
import { executeSandbox, parseCode } from '../api';

export default function SandboxConsole({ code, language, endpoints: propEndpoints, onGenerate }) {
  const [endpoints, setEndpoints] = useState(propEndpoints || []);
  const [selectedEp, setSelectedEp] = useState(null);
  const [requestBody, setRequestBody] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);

  useEffect(() => {
    setEndpoints(propEndpoints || []);
  }, [propEndpoints]);

  const handleParse = async () => {
    if (!code.trim()) return;
    setParsing(true);
    try {
      const result = await parseCode(code, language);
      setEndpoints(result.endpoints || []);
    } catch (err) {
      console.error(err);
    } finally {
      setParsing(false);
    }
  };

  const handleExecute = async () => {
    if (!selectedEp) return;
    setLoading(true);
    try {
      const result = await executeSandbox(
        code,
        selectedEp.path,
        selectedEp.method,
        requestBody || null
      );
      setResponse(result);
    } catch (err) {
      setResponse({
        status_code: 500,
        body: { error: err.message },
        latency_ms: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  if (endpoints.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-icon">🏖️</span>
        <h3>No endpoints parsed yet</h3>
        <p>Parse your code first to see available endpoints</p>
        <button className="btn btn-primary btn-sm" onClick={handleParse} disabled={parsing}>
          {parsing ? '⏳ Parsing...' : '🔍 Parse Code'}
        </button>
      </div>
    );
  }

  return (
    <div className="sandbox-console">
      {/* Endpoint List */}
      <div className="sandbox-endpoint-list">
        {endpoints.map((ep, i) => (
          <div
            key={i}
            className={`sandbox-endpoint ${selectedEp === ep ? 'selected' : ''}`}
            onClick={() => {
              setSelectedEp(ep);
              setResponse(null);
              // Pre-fill body for POST/PUT
              if (['POST', 'PUT', 'PATCH'].includes(ep.method)) {
                const fields = ep.body_fields || ep.parameters?.filter(p => p.location === 'body').map(p => p.name) || [];
                if (fields.length > 0) {
                  const body = {};
                  fields.forEach(f => { body[f] = 'example'; });
                  setRequestBody(JSON.stringify(body, null, 2));
                } else {
                  setRequestBody('{\n  \n}');
                }
              } else {
                setRequestBody('');
              }
            }}
          >
            <span className={`method-badge method-${ep.method}`}>{ep.method}</span>
            <span className="sandbox-path">{ep.path}</span>
          </div>
        ))}
      </div>

      {/* Request Area */}
      {selectedEp && (
        <div className="sandbox-request-area">
          {['POST', 'PUT', 'PATCH'].includes(selectedEp.method) && (
            <div className="sandbox-input-group">
              <label>Request Body (JSON)</label>
              <textarea
                className="sandbox-input"
                rows={5}
                value={requestBody}
                onChange={e => setRequestBody(e.target.value)}
                placeholder='{ "key": "value" }'
              />
            </div>
          )}

          <button
            className="btn btn-primary"
            onClick={handleExecute}
            disabled={loading}
            style={{ alignSelf: 'flex-start' }}
          >
            {loading ? (
              <><span className="spinner" style={{width:14,height:14,borderWidth:2}}></span> Executing...</>
            ) : (
              `▶ Send ${selectedEp.method} ${selectedEp.path}`
            )}
          </button>

          {/* Response */}
          {response && (
            <div className="sandbox-response">
              <div className="sandbox-response-header">
                <span className={`status-badge status-${response.status_code}`}>
                  {response.status_code}
                </span>
                <span className="latency-tag">{response.latency_ms}ms • sandbox</span>
              </div>
              <div className="response-body">
                {JSON.stringify(response.body, null, 2)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
