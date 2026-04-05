"use client";

export default function SimulationResults({ result }) {
  if (!result) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">Validation Protocol</div>
        </div>
        <div className="empty-state" style={{ padding: '40px 0' }}>
          <div className="empty-state-text" style={{ fontSize: '14px', opacity: 0.5 }}>
            Synthesized validation logs will be generated post-simulation.
          </div>
        </div>
      </div>
    );
  }

  const metrics = [
    { label: "INPUT CARDINALITY", value: result.input_rows?.toLocaleString() || "0" },
    { label: "OUTPUT CARDINALITY", value: result.output_rows?.toLocaleString() || "0" },
    { label: "LATENCY", value: `${(result.execution_time_ms || 0).toFixed(0)}ms` },
    { label: "SYSTEM STATE", value: result.success ? "NOMINAL" : "CRITICAL" },
  ];

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Validation Protocol</div>
        <div className={`section-badge ${result.success ? "badge-success" : "badge-error"}`} style={{ padding: '4px 12px', fontSize: '11px', fontWeight: '800', borderRadius: '4px' }}>
          {result.success ? "SYSTEM NOMINAL" : "VALIDATION FAULT"}
        </div>
      </div>

      <div className="sim-metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.5px', background: 'var(--border-strong)', border: '1.5px solid var(--border-strong)', borderBottom: 'none', borderTop: 'none', marginTop: '24px' }}>
        {metrics.map((m, i) => (
          <div className="sim-metric" key={i} style={{ padding: '24px', background: '#fff', textAlign: 'left', transition: 'background 0.2s' }}>
            <div className="sim-metric-label" style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', marginBottom: '10px', letterSpacing: '0.05em' }}>{m.label}</div>
            <div className="sim-metric-value" style={{ fontSize: '24px', fontWeight: '900', color: i === 3 ? (result.success ? 'var(--brand-success)' : 'var(--brand-error)') : 'var(--text-primary)' }}>{m.value}</div>
          </div>
        ))}
      </div>

      {(result.logs?.length > 0 || result.errors?.length > 0) && (
        <div 
          style={{ 
            padding: '32px', background: '#0f172a', border: '1.5px solid var(--border-strong)', 
            overflowX: 'auto', overflowY: 'auto', maxHeight: '450px' 
          }} 
          className="custom-scroll"
        >
          <div style={{ fontSize: '11px', fontWeight: '900', color: '#64748b', marginBottom: '24px', letterSpacing: '0.1em' }}>AGGREGATED EXECUTION STREAM</div>
          {result.errors?.map((log, i) => (
            <div key={`err-${i}`} style={{ color: '#fda4af', fontSize: '13px', marginBottom: '12px', display: 'flex', gap: '16px', fontFamily: 'var(--font-mono)', borderBottom: '1px solid rgba(244, 63, 94, 0.1)', paddingBottom: '8px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              <span style={{ opacity: 0.6, fontWeight: '800', flexShrink: 0 }}>[ ERR ]</span> 
              <div style={{ flex: 1 }}>{log}</div>
            </div>
          ))}
          {result.logs?.map((log, i) => (
            <div key={`log-${i}`} style={{ color: '#6ee7b7', fontSize: '13px', marginBottom: '10px', display: 'flex', gap: '16px', fontFamily: 'var(--font-mono)', borderBottom: '1px solid rgba(16, 185, 129, 0.1)', paddingBottom: '8px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
              <span style={{ opacity: 0.6, fontWeight: '800', flexShrink: 0 }}>[ INF ]</span> 
              <div style={{ flex: 1 }}>{log}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
