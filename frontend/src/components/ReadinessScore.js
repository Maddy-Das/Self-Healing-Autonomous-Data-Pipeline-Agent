"use client";

export default function ReadinessScore({ readiness }) {
  if (!readiness || !readiness.overall) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">
            Deployment Readiness
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-text" style={{ fontSize: '13px', opacity: 0.5 }}>
            Synthesized assessment will be generated post-healing cycle.
          </div>
        </div>
      </div>
    );
  }

  const score = readiness.overall || 0;

  const getColor = (val) => {
    if (val >= 80) return "var(--brand-success)";
    if (val >= 60) return "var(--brand-warning)";
    return "var(--brand-error)";
  };

  const breakdownItems = [
    { label: "Data Quality", value: readiness.data_quality || 0 },
    { label: "Code Architecture", value: readiness.code_quality || 0 },
    { label: "DAG Consistency", value: readiness.dag_validity || 0 },
    { label: "Error Resilience", value: readiness.error_handling || 0 },
  ];

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Deployment Readiness</div>
      </div>

      <div className="readiness-container" style={{ textAlign: 'left', padding: '24px 0' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '16px', marginBottom: '24px' }}>
          <div style={{ fontSize: '48px', fontWeight: '900', color: 'var(--text-primary)', letterSpacing: '-0.04em', lineHeight: 1 }}>{score}</div>
          <div style={{ fontSize: '12px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>Percent Readiness</div>
          <div style={{ marginLeft: 'auto', flex: 1, paddingBottom: '12px' }}>
            <div style={{ height: '8px', background: 'var(--border-subtle)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${score}%`, height: '100%', background: getColor(score), transition: 'width 1s ease' }} />
            </div>
          </div>
        </div>

        <div className="score-breakdown" style={{ width: '100%' }}>
          {breakdownItems.map((item, idx) => (
            <div className="score-item" key={idx} style={{ 
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', 
              padding: '16px 0', borderBottom: '1px solid var(--border-subtle)' 
            }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '700', width: '140px' }}>{item.label}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1, marginLeft: '40px' }}>
                <div style={{ flex: 1, height: '4px', background: 'var(--border-subtle)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ width: `${item.value}%`, height: '100%', background: getColor(item.value), transition: 'width 1.5s ease' }} />
                </div>
                <span style={{ fontSize: '12px', fontWeight: '800', color: 'var(--text-primary)', minWidth: '40px', textAlign: 'right' }}>
                  {item.value}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
