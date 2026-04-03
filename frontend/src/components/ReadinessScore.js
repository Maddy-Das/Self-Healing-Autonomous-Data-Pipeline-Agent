"use client";

export default function ReadinessScore({ readiness }) {
  if (!readiness || !readiness.overall) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">🎯</span> Readiness Score
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📈</div>
          <div className="empty-state-text">
            Production readiness score will appear after healing
          </div>
        </div>
      </div>
    );
  }

  const score = readiness.overall || 0;
  const circumference = 2 * Math.PI * 72;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (val) => {
    if (val >= 80) return "var(--accent-emerald)";
    if (val >= 60) return "var(--accent-amber)";
    return "var(--accent-rose)";
  };

  const breakdownItems = [
    { label: "Data Quality", value: readiness.data_quality || 0 },
    { label: "Code Quality", value: readiness.code_quality || 0 },
    { label: "DAG Validity", value: readiness.dag_validity || 0 },
    { label: "Error Handling", value: readiness.error_handling || 0 },
    { label: "Security", value: readiness.security || 0 },
    { label: "Performance", value: readiness.performance || 0 },
  ];

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">🎯</span> Readiness Score
        </div>
        <span
          className={`section-badge ${score >= 80 ? "badge-success" : score >= 60 ? "badge-warning" : "badge-error"}`}
        >
          {score >= 80 ? "Production Ready" : score >= 60 ? "Needs Review" : "Not Ready"}
        </span>
      </div>

      <div className="readiness-container">
        <div className="score-gauge">
          <svg className="score-circle" width="180" height="180" viewBox="0 0 180 180">
            <circle className="score-track" cx="90" cy="90" r="72" />
            <circle
              className="score-fill"
              cx="90"
              cy="90"
              r="72"
              stroke={getColor(score)}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="score-value">
            <div className="score-number" style={{ color: getColor(score) }}>
              {score}
            </div>
            <div className="score-label">/ 100</div>
          </div>
        </div>

        <div className="score-breakdown">
          {breakdownItems.map((item, idx) => (
            <div className="score-item" key={idx}>
              <span className="score-item-label">{item.label}</span>
              <div className="score-item-bar">
                <div
                  className="score-item-fill"
                  style={{
                    width: `${item.value}%`,
                    background: getColor(item.value),
                  }}
                />
              </div>
              <span className="score-item-value" style={{ color: getColor(item.value) }}>
                {item.value}
              </span>
            </div>
          ))}
        </div>

        {readiness.details?.length > 0 && (
          <div style={{ width: "100%", marginTop: 12 }}>
            {readiness.details.map((detail, i) => (
              <div
                key={i}
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  padding: "4px 0",
                  borderBottom: "1px solid rgba(255,255,255,0.03)",
                }}
              >
                • {detail}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
