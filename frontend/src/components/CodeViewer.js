"use client";
import { useState } from "react";

export default function CodeViewer({ artifacts }) {
  const [activeTab, setActiveTab] = useState("etl");

  const tabs = [
    { id: "etl", label: "Logic Synthesis", code: artifacts?.etl_code, ext: "py" },
    { id: "sql", label: "Schema Manifest", code: artifacts?.sql_schema, ext: "sql" },
    { id: "dag", label: "Orchestration DAG", code: artifacts?.airflow_dag, ext: "py" },
  ];

  const activeTabObj = tabs.find((t) => t.id === activeTab);
  const currentCode = activeTabObj?.code || "";

  const copyCode = () => {
    navigator.clipboard.writeText(currentCode);
  };

  if (!artifacts?.etl_code && !artifacts?.sql_schema && !artifacts?.airflow_dag) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">Logic Synthesis</div>
        </div>
        <div className="empty-state">
          <div className="empty-state-text" style={{ fontSize: '13px', opacity: 0.5 }}>
            Synthesized logic artifacts will be available post-synthesis.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Logic Synthesis</div>
        <div className="section-badge badge-success" style={{ padding: '2px 8px', fontSize: '10px' }}>SYNTHESIZED</div>
      </div>

      <div className="code-tabs" style={{ marginTop: '24px', display: 'flex', gap: '4px', background: '#f1f5f9', padding: '4px', borderRadius: '8px' }}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`code-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
            style={{ 
              display: 'flex', alignItems: 'center', gap: '8px', 
              padding: '6px 12px', borderRadius: '6px',
              background: activeTab === tab.id ? '#fff' : 'transparent',
              border: activeTab === tab.id ? '1px solid var(--border-strong)' : '1px solid transparent',
              color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
              fontSize: '13px', fontWeight: '700', cursor: 'pointer', flex: 1
            }}
          >
            <span style={{ fontSize: '10px', opacity: 0.4 }}>{tab.ext}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{ position: 'relative', marginTop: '1px' }}>
        <button 
          onClick={copyCode} 
          style={{ 
            position: 'absolute', top: '16px', right: '16px', padding: '6px 12px', 
            background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', 
            borderRadius: '6px', color: '#cbd5e1', fontSize: '11px', cursor: 'pointer',
            transition: 'all 0.1s', fontWeight: '700', zIndex: 10
          }}
        >
          Copy Logic
        </button>
        <div className="code-block custom-scroll" style={{ background: '#0f172a', border: '1px solid #0f172a', borderRadius: '0 0 12px 12px', padding: '32px', minHeight: '400px', maxHeight: '600px', overflowY: 'auto' }}>
          <pre style={{ margin: 0, overflowX: 'auto', fontSize: '13px', fontFamily: 'var(--font-mono)', lineHeight: 1.8, color: '#e2e8f0', letterSpacing: '0.01em' }}>
            {currentCode || "// Synthesis pending artifacts..."}
          </pre>
        </div>
      </div>
    </div>
  );
}
