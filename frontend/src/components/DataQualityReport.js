"use client";

export default function DataQualityReport({ report }) {
  if (!report || !report.checks) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">🛡️</span> Data Quality & Security
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-text">
            Quality and security checks will run after data upload
          </div>
        </div>
      </div>
    );
  }

  const severityOrder = { critical: 0, warning: 1, info: 2 };
  const sortedChecks = [...report.checks].sort(
    (a, b) => (severityOrder[a.severity] || 3) - (severityOrder[b.severity] || 3)
  );

  const severityIcon = { critical: "🔴", warning: "🟡", info: "🔵" };
  const categoryIcon = {
    data_quality: "📊",
    security: "🔒",
    schema_drift: "📐",
    performance: "⚡",
  };

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">🛡️</span> Data Quality & Security
        </div>
        <span
          className={`section-badge ${
            report.quality_score >= 80
              ? "badge-success"
              : report.quality_score >= 60
              ? "badge-warning"
              : "badge-error"
          }`}
        >
          Score: {report.quality_score}/100
        </span>
      </div>

      {/* Summary Metrics */}
      <div className="sim-metrics" style={{ marginBottom: 16 }}>
        <div className="sim-metric">
          <div className="sim-metric-value" style={{ color: "var(--accent-rose)" }}>
            {report.critical_count || 0}
          </div>
          <div className="sim-metric-label">Critical</div>
        </div>
        <div className="sim-metric">
          <div className="sim-metric-value" style={{ color: "var(--accent-amber)" }}>
            {report.warning_count || 0}
          </div>
          <div className="sim-metric-label">Warnings</div>
        </div>
        <div className="sim-metric">
          <div className="sim-metric-value" style={{ color: "var(--accent-cyan)" }}>
            {report.info_count || 0}
          </div>
          <div className="sim-metric-label">Info</div>
        </div>
        <div className="sim-metric">
          <div
            className="sim-metric-value"
            style={{ color: report.pii_detected ? "var(--accent-rose)" : "var(--accent-emerald)" }}
          >
            {report.pii_detected ? "⚠️" : "✓"}
          </div>
          <div className="sim-metric-label">PII Scan</div>
        </div>
      </div>

      {/* PII Alert */}
      {report.pii_detected && report.pii_columns?.length > 0 && (
        <div
          style={{
            padding: "12px 16px",
            background: "rgba(244, 63, 94, 0.08)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "var(--radius-md)",
            marginBottom: 16,
            fontSize: 13,
          }}
        >
          <strong style={{ color: "var(--accent-rose)" }}>🔒 PII Detected:</strong>{" "}
          <span style={{ color: "var(--text-secondary)" }}>
            Columns [{report.pii_columns.join(", ")}] contain personally identifiable
            information. Masking/encryption recommendations included below.
          </span>
        </div>
      )}

      {/* Issue List */}
      <div style={{ maxHeight: 300, overflowY: "auto" }}>
        {sortedChecks.map((check, i) => (
          <div
            key={i}
            style={{
              padding: "10px 14px",
              marginBottom: 6,
              borderRadius: "var(--radius-sm)",
              background:
                check.severity === "critical"
                  ? "rgba(244, 63, 94, 0.06)"
                  : check.severity === "warning"
                  ? "rgba(245, 158, 11, 0.06)"
                  : "rgba(6, 182, 212, 0.04)",
              borderLeft: `3px solid ${
                check.severity === "critical"
                  ? "var(--accent-rose)"
                  : check.severity === "warning"
                  ? "var(--accent-amber)"
                  : "var(--accent-cyan)"
              }`,
              fontSize: 13,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <span>{severityIcon[check.severity] || "ℹ️"}</span>
              <span>{categoryIcon[check.category] || "📋"}</span>
              <strong style={{ color: "var(--text-primary)" }}>
                {check.column !== "_all_" ? `[${check.column}]` : ""} {check.description}
              </strong>
            </div>
            {check.recommendation && (
              <div style={{ color: "var(--text-muted)", fontSize: 12, paddingLeft: 40 }}>
                💡 {check.recommendation}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
