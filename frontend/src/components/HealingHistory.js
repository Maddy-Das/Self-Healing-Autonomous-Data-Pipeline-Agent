"use client";

export default function HealingHistory({ history }) {
  if (!history || history.length === 0) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">🔄</span> Healing History
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🩺</div>
          <div className="empty-state-text">
            Self-healing iterations will be tracked here
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">🔄</span> Healing History
        </div>
        <span className="section-badge badge-info">
          {history.length} iteration{history.length !== 1 ? "s" : ""}
        </span>
      </div>

      <div className="healing-timeline">
        {history.map((entry, idx) => (
          <div className="healing-entry" key={idx}>
            <div className={`healing-dot ${entry.issues_found?.length === 0 ? "fixed" : ""}`} />
            <div className="healing-iteration-title">
              Iteration {entry.iteration}
            </div>

            {entry.issues_found?.length > 0 && (
              <ul className="healing-issues">
                {entry.issues_found.map((issue, i) => (
                  <li className="healing-issue found" key={`issue-${i}`}>
                    <span>⚠️</span>
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            )}

            {entry.fixes_applied?.length > 0 && (
              <ul className="healing-issues" style={{ marginTop: 8 }}>
                {entry.fixes_applied.map((fix, i) => (
                  <li className="healing-issue fix" key={`fix-${i}`}>
                    <span>✅</span>
                    <span>{fix}</span>
                  </li>
                ))}
              </ul>
            )}

            {entry.issues_found?.length === 0 && (
              <div
                className="healing-issue fix"
                style={{ display: "inline-flex", marginTop: 4 }}
              >
                <span>🎉</span>
                <span>No issues found — pipeline is clean!</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
