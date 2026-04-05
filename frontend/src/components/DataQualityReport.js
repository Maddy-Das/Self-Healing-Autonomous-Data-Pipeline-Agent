"use client";

export default function DataQualityReport({ report }) {
  if (!report || !report.checks) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">
            Integrity Assessment
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-text" style={{ fontSize: '13px', opacity: 0.5 }}>
            Synthesized assessment will be generated post-upload.
          </div>
        </div>
      </div>
    );
  }

  const severityOrder = { critical: 0, warning: 1, info: 2 };
  const sortedChecks = [...report.checks].sort(
    (a, b) => (severityOrder[a.severity] || 3) - (severityOrder[b.severity] || 3)
  );

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1px solid var(--border-subtle)', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Integrity Assessment</div>
        <div
          className={`section-badge ${
            report.quality_score >= 80 ? "badge-success" : report.quality_score >= 60 ? "badge-warning" : "badge-error"
          }`}
          style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '4px' }}
        >
          {report.quality_score}% Confidence
        </div>
      </div>

      <div className="sim-metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1px', background: 'var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="sim-metric" style={{ padding: '24px', background: '#fff', textAlign: 'left' }}>
          <div className="sim-metric-label" style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '8px' }}>CRITICAL</div>
          <div className="sim-metric-value" style={{ fontSize: '28px', fontWeight: '800', 
            color: report.critical_count > 0 ? 'var(--brand-error)' : 'var(--text-primary)' 
          }}>
            {report.critical_count || 0}
          </div>
        </div>
        <div className="sim-metric" style={{ padding: '24px', background: '#fff', textAlign: 'left' }}>
          <div className="sim-metric-label" style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '8px' }}>WARNING</div>
          <div className="sim-metric-value" style={{ fontSize: '28px', fontWeight: '800', 
            color: report.warning_count > 0 ? 'var(--brand-warning)' : 'var(--text-primary)' 
          }}>
            {report.warning_count || 0}
          </div>
        </div>
        <div className="sim-metric" style={{ padding: '24px', background: '#fff', textAlign: 'left' }}>
          <div className="sim-metric-label" style={{ fontSize: '10px', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '8px' }}>INFO</div>
          <div className="sim-metric-value" style={{ fontSize: '28px', fontWeight: '800' }}>
            {report.info_count || 0}
          </div>
        </div>
      </div>

      <div style={{ maxHeight: 350, overflowY: "auto" }} className="custom-scroll">
        {sortedChecks.map((check, i) => (
          <div
            key={i}
            style={{
              padding: "16px 0",
              borderBottom: "1px solid var(--border-subtle)",
              fontSize: 13,
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
              <span style={{ 
                width: '8px', height: '8px', borderRadius: '50%', marginTop: '5px',
                background: check.severity === 'critical' ? 'var(--brand-error)' : 
                            check.severity === 'warning' ? 'var(--brand-warning)' : 'var(--brand-primary)'
              }} />
              <div style={{ flex: 1 }}>
                <div style={{ color: "var(--text-primary)", fontWeight: 700, fontSize: '14px' }}>
                  {check.column !== "_all_" ? <span style={{ color: 'var(--brand-primary)', marginRight: '6px' }}>[{check.column}]</span> : ""}
                  {check.description}
                </div>
                {check.recommendation && (
                  <div style={{ color: "var(--text-secondary)", fontSize: '12px', marginTop: 6 }}>
                    <span style={{ fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', fontSize: '10px', marginRight: '6px' }}>Resolution</span>
                    {check.recommendation}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
