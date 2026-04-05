"use client";
import { useState } from "react";

export default function ReasoningTraces({ builderReasoning, healerReasoning }) {
  const [openPanels, setOpenPanels] = useState({ builder: true, healer: true });

  const toggle = (key) => {
    setOpenPanels((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const panels = [
    {
      key: "builder",
      label: "Architectural Synthesis",
      content: builderReasoning,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/><circle cx="12" cy="12" r="3"/></svg>
      )
    },
    {
      key: "healer",
      label: "Delta Resolution Synthesis",
      content: healerReasoning,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.77 3.77z"/></svg>
      )
    },
  ];

  const hasContent = builderReasoning || healerReasoning;

  if (!hasContent) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">Agentic Reasoning</div>
        </div>
        <div className="empty-state">
          <div className="empty-state-text" style={{ fontSize: '13px', opacity: 0.5 }}>
            Synthesized reasoning traces will be available post-synthesis.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent' }}>
        <div className="section-title">Agentic Reasoning</div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1px', background: 'var(--border-subtle)', marginTop: '24px' }}>
        {panels.map((panel) =>
          panel.content && (
            <div className="reasoning-panel" key={panel.key} style={{ background: '#fff', borderBottom: '1px solid var(--border-subtle)' }}>
              <div
                className="reasoning-header"
                onClick={() => toggle(panel.key)}
                style={{ padding: '16px 20px', background: '#fcfcfd', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{panel.icon}</span>
                  <span className="reasoning-label" style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>{panel.label}</span>
                </div>
                <div
                  className={`reasoning-expand ${openPanels[panel.key] ? "open" : ""}`}
                  style={{ transition: 'transform 0.4s', transform: openPanels[panel.key] ? 'rotate(180deg)' : 'rotate(0deg)', opacity: 0.5 }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
              </div>
              {openPanels[panel.key] && (
                <div className="reasoning-content" style={{ padding: '24px', background: '#ffffff', fontSize: '14px', lineHeight: '1.8', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', whiteSpace: 'pre-wrap', maxHeight: '450px', overflowY: 'auto', fontFamily: 'var(--font-mono)' }}>
                  {panel.content}
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
}
