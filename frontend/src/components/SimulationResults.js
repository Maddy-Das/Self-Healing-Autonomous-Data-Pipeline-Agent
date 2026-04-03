"use client";

export default function SimulationResults({ result }) {
  if (!result) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">🧪</span> Simulation Results
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🔬</div>
          <div className="empty-state-text">
            Simulation results will appear here after pipeline execution
          </div>
        </div>
      </div>
    );
  }

  const metrics = [
    { label: "Input Rows", value: result.input_rows?.toLocaleString() || "0" },
    { label: "Output Rows", value: result.output_rows?.toLocaleString() || "0" },
    { label: "Exec Time", value: `${(result.execution_time_ms || 0).toFixed(0)}ms` },
    { label: "Status", value: result.success ? "PASS" : "FAIL" },
  ];

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">🧪</span> Simulation Results
        </div>
        <span className={`section-badge ${result.success ? "badge-success" : "badge-error"}`}>
          {result.success ? "Passed" : "Failed"}
        </span>
      </div>

      <div className="sim-metrics">
        {metrics.map((m, i) => (
          <div className="sim-metric" key={i}>
            <div className="sim-metric-value">{m.value}</div>
            <div className="sim-metric-label">{m.label}</div>
          </div>
        ))}
      </div>

      {(result.logs?.length > 0 || result.errors?.length > 0) && (
        <div className="sim-logs">
          {result.errors?.map((log, i) => (
            <div key={`err-${i}`} className="sim-log-entry error">❌ {log}</div>
          ))}
          {result.logs?.map((log, i) => (
            <div key={`log-${i}`} className="sim-log-entry success">✓ {log}</div>
          ))}
        </div>
      )}

      {/* DAG Validation */}
      {result.dag_validation && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: "var(--text-secondary)" }}>
            DAG Validation
          </div>
          <div className="sim-metrics">
            <div className="sim-metric">
              <div className="sim-metric-value">{result.dag_validation.valid_syntax ? "✓" : "✗"}</div>
              <div className="sim-metric-label">Syntax</div>
            </div>
            <div className="sim-metric">
              <div className="sim-metric-value">{result.dag_validation.task_count || 0}</div>
              <div className="sim-metric-label">Tasks</div>
            </div>
            <div className="sim-metric">
              <div className="sim-metric-value">{result.dag_validation.has_schedule ? "✓" : "✗"}</div>
              <div className="sim-metric-label">Schedule</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
