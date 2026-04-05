"use client";
export default function Header({ status }) {
  const statusMap = {
    idle: { label: "System Ready", className: "idle" },
    profiling: { label: "Profiling Source...", className: "active" },
    generating: { label: "Synthesizing Architecture...", className: "active" },
    simulating: { label: "Running Validations...", className: "active" },
    healing: { label: "Delta Resolution...", className: "active" },
    complete: { label: "Infrastructure Ready", className: "complete" },
    error: { label: "Execution Fault", className: "error" },
  };

  const s = statusMap[status] || statusMap.idle;

  const getStatusColor = () => {
    if (s.className === 'active') return 'var(--brand-primary)';
    if (s.className === 'complete') return 'var(--brand-success)';
    if (s.className === 'error') return 'var(--brand-error)';
    return 'var(--text-muted)';
  };

  return (
    <div className={`sidebar-status-widget ${s.className}`} style={{ 
      fontSize: '12px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '10px',
      color: 'var(--text-primary)'
    }}>
      <div className="status-dot-container" style={{ position: 'relative', width: '8px', height: '8px' }}>
        <span className={`status-dot ${s.className}`} style={{ 
          position: 'absolute', width: '100%', height: '100%', borderRadius: '50%',
          background: getStatusColor()
        }} />
        {s.className === 'active' && (
          <span className="status-dot-pulse" style={{ 
            position: 'absolute', width: '100%', height: '100%', borderRadius: '50%',
            background: getStatusColor(), opacity: 0.4,
            animation: 'pulse 1.5s cubic-bezier(0, 0, 0.2, 1) infinite'
          }} />
        )}
      </div>
      {s.label}
      <style jsx>{`
        @keyframes pulse {
          0% { transform: scale(1); opacity: 0.4; }
          100% { transform: scale(2.5); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
