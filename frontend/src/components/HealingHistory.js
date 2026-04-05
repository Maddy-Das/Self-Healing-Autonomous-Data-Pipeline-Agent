"use client";

export default function HealingHistory({ history }) {
  if (!history || history.length === 0) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">Resolution History</div>
        </div>
        <div className="empty-state">
          <div className="empty-state-text" style={{ fontSize: '13px', opacity: 0.5 }}>
            Synthesized resolution logs will be generated post-healing cycle.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Resolution History</div>
        <div className="section-badge badge-info" style={{ fontSize: '10px' }}>
          {history.length} Autonomous Iteration{history.length !== 1 ? "s" : ""}
        </div>
      </div>

      <div style={{ position: 'relative', paddingLeft: '32px', borderLeft: '1px solid var(--border-strong)', marginLeft: '12px', marginTop: '24px' }}>
        {history.map((entry, idx) => (
          <div key={idx} style={{ marginBottom: '40px', position: 'relative' }}>
            <div style={{ 
              position: 'absolute', left: '-36.5px', top: '0', width: '8px', height: '8px', 
              borderRadius: '50%', background: entry.issues_found?.length === 0 ? 'var(--brand-success)' : 'var(--brand-primary)',
              border: '2px solid #fff'
            }} />
            
            <div style={{ fontSize: '11px', fontWeight: '800', marginBottom: '16px', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              CYCLE v0.{entry.iteration} AUDIT TRACE
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {entry.issues_found?.length > 0 && entry.issues_found.map((issue, i) => (
                <div key={`issue-${i}`} style={{ fontSize: '13px', color: 'var(--brand-error)', background: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-strong)', display: 'flex', gap: '12px' }}>
                  <span style={{ fontWeight: '800', opacity: 0.5 }}>!</span> {issue}
                </div>
              ))}
              
              {entry.fixes_applied?.length > 0 && entry.fixes_applied.map((fix, i) => (
                <div key={`fix-${i}`} style={{ fontSize: '13px', color: 'var(--brand-success)', background: '#fff', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-strong)', display: 'flex', gap: '12px' }}>
                  <span style={{ fontWeight: '800', opacity: 0.5 }}>+</span> {fix}
                </div>
              ))}

              {entry.issues_found?.length === 0 && (
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', paddingLeft: '8px' }}>
                  System state nominal. No delta required.
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
