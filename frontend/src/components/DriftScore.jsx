import { useEffect, useState } from 'react';

export default function DriftScore({ result }) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    if (result) {
      let start = 0;
      const target = result.drift_score;
      const duration = 1200;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        setAnimatedScore(Math.round(eased * target * 10) / 10);
        if (progress < 1) requestAnimationFrame(animate);
      };
      animate();
    }
  }, [result]);

  if (!result) {
    return (
      <div className="empty-state">
        <span className="empty-icon">📊</span>
        <h3>No drift analysis yet</h3>
        <p>Paste your API code and existing docs, then click "Analyze Drift"</p>
      </div>
    );
  }

  const getColor = (score) => {
    if (score < 20) return 'var(--accent-green)';
    if (score < 40) return '#8ac926';
    if (score < 60) return 'var(--accent-orange)';
    if (score < 80) return '#ff6b35';
    return 'var(--accent-red)';
  };

  const color = getColor(result.drift_score);
  const circumference = 2 * Math.PI * 72;
  const dashOffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="drift-dashboard">
      {/* Gauge */}
      <div className="drift-gauge">
        <div className="gauge-circle">
          <svg width="180" height="180" viewBox="0 0 180 180">
            <circle className="gauge-bg" cx="90" cy="90" r="72" />
            <circle
              className="gauge-fill"
              cx="90" cy="90" r="72"
              stroke={color}
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
            />
          </svg>
          <div className="gauge-value">
            <div className="number" style={{ color }}>{animatedScore}</div>
            <div className="label">Drift Score</div>
          </div>
        </div>
        <div className="drift-quality">{result.quality}</div>
        <p className="drift-summary">{result.summary}</p>
      </div>

      {/* Stats */}
      <div className="drift-stats">
        <div className="drift-stat">
          <div className="stat-value">{result.total_endpoints_in_code}</div>
          <div className="stat-label">In Code</div>
        </div>
        <div className="drift-stat">
          <div className="stat-value">{result.documented_endpoints}</div>
          <div className="stat-label">Documented</div>
        </div>
        <div className="drift-stat">
          <div className="stat-value">{result.missing_endpoints?.length || 0}</div>
          <div className="stat-label">Missing</div>
        </div>
      </div>

      {/* Issues */}
      {result.missing_endpoints?.length > 0 && (
        <div>
          <h4 style={{fontSize:'0.875rem',fontWeight:600,marginBottom:'8px',color:'var(--text-secondary)'}}>
            Missing Endpoints
          </h4>
          <div className="drift-issues">
            {result.missing_endpoints.map((ep, i) => (
              <div key={i} className="drift-issue">
                <span className="issue-icon">❌</span>
                <code style={{fontSize:'0.8125rem',fontFamily:'var(--font-mono)',color:'var(--accent-red)'}}>{ep}</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.outdated_endpoints?.length > 0 && (
        <div>
          <h4 style={{fontSize:'0.875rem',fontWeight:600,marginBottom:'8px',color:'var(--text-secondary)'}}>
            Outdated Endpoints
          </h4>
          <div className="drift-issues">
            {result.outdated_endpoints.map((ep, i) => (
              <div key={i} className="drift-issue">
                <span className="issue-icon">⚠️</span>
                <div>
                  <code style={{fontSize:'0.8125rem',fontFamily:'var(--font-mono)',color:'var(--accent-orange)'}}>
                    {ep.method} {ep.path}
                  </code>
                  {ep.issues?.map((issue, j) => (
                    <div key={j} style={{fontSize:'0.75rem',color:'var(--text-tertiary)',marginTop:'2px'}}>{issue}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.extra_in_docs?.length > 0 && (
        <div>
          <h4 style={{fontSize:'0.875rem',fontWeight:600,marginBottom:'8px',color:'var(--text-secondary)'}}>
            Ghost Endpoints (in docs, not in code)
          </h4>
          <div className="drift-issues">
            {result.extra_in_docs.map((ep, i) => (
              <div key={i} className="drift-issue">
                <span className="issue-icon">👻</span>
                <code style={{fontSize:'0.8125rem',fontFamily:'var(--font-mono)',color:'var(--accent-purple)'}}>{ep}</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Breakdown */}
      {result.breakdown && (
        <div style={{marginTop:'8px'}}>
          <h4 style={{fontSize:'0.875rem',fontWeight:600,marginBottom:'8px',color:'var(--text-secondary)'}}>
            Score Breakdown
          </h4>
          <div style={{display:'flex',flexDirection:'column',gap:'6px'}}>
            {Object.entries(result.breakdown).map(([key, val]) => (
              <div key={key} style={{display:'flex',justifyContent:'space-between',fontSize:'0.8125rem'}}>
                <span style={{color:'var(--text-tertiary)'}}>{key.replace(/_/g,' ').replace(/penalty/,'')}</span>
                <span style={{fontFamily:'var(--font-mono)',color: val > 0 ? 'var(--accent-orange)' : 'var(--accent-green)'}}>
                  +{val}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
