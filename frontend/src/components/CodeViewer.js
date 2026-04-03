"use client";
import { useState } from "react";

export default function CodeViewer({ artifacts }) {
  const [activeTab, setActiveTab] = useState("etl");

  const tabs = [
    { id: "etl", label: "ETL Script", code: artifacts?.etl_code },
    { id: "sql", label: "SQL Schema", code: artifacts?.sql_schema },
    { id: "dag", label: "Airflow DAG", code: artifacts?.airflow_dag },
  ];

  const currentCode = tabs.find((t) => t.id === activeTab)?.code || "";

  const copyCode = () => {
    navigator.clipboard.writeText(currentCode);
  };

  if (!artifacts?.etl_code && !artifacts?.sql_schema && !artifacts?.airflow_dag) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">💻</span> Generated Code
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <div className="empty-state-text">
            Code will appear here after pipeline generation
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">💻</span> Generated Code
        </div>
        <span className="section-badge badge-info">
          {tabs.filter((t) => t.code).length} files
        </span>
      </div>

      <div className="code-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`code-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
            {tab.code ? " ✓" : ""}
          </button>
        ))}
      </div>

      <div className="code-block">
        <button className="code-copy-btn" onClick={copyCode} title="Copy code">
          📋 Copy
        </button>
        <pre>{currentCode || "No code generated for this tab."}</pre>
      </div>
    </div>
  );
}
