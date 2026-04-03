"use client";
export default function Header({ status }) {
  const statusMap = {
    idle: { label: "Ready", className: "idle" },
    profiling: { label: "Profiling Data…", className: "active" },
    generating: { label: "Building Pipeline…", className: "active" },
    simulating: { label: "Running Simulation…", className: "active" },
    healing: { label: "Self-Healing…", className: "active" },
    complete: { label: "Pipeline Ready", className: "complete" },
    error: { label: "Error", className: "error" },
  };

  const s = statusMap[status] || statusMap.idle;

  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-brand">
          <div className="header-logo">⚡</div>
          <div>
            <div className="header-title">Self-Healing Pipeline Agent</div>
            <div className="header-subtitle">
              AI-Powered Autonomous Data Pipeline Builder
            </div>
          </div>
        </div>
        <div className={`header-status ${s.className}`}>
          <span
            className={`status-dot ${s.className === "active" ? "active" : ""}`}
          />
          {s.label}
        </div>
      </div>
    </header>
  );
}
