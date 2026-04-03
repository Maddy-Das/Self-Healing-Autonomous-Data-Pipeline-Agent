"use client";
import { useState } from "react";

export default function ReasoningTraces({ builderReasoning, healerReasoning }) {
  const [openPanels, setOpenPanels] = useState({});

  const toggle = (key) => {
    setOpenPanels((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const panels = [
    {
      key: "builder",
      label: "🏗️ Builder Agent Reasoning",
      content: builderReasoning,
    },
    {
      key: "healer",
      label: "🔧 Healing Agent Reasoning",
      content: healerReasoning,
    },
  ];

  const hasContent = builderReasoning || healerReasoning;

  if (!hasContent) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">🧠</span> Reasoning Traces
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">💭</div>
          <div className="empty-state-text">
            Agent reasoning will appear here during pipeline generation
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">🧠</span> Reasoning Traces
        </div>
        <span className="section-badge badge-info">AI Thoughts</span>
      </div>

      {panels.map(
        (panel) =>
          panel.content && (
            <div className="reasoning-panel" key={panel.key}>
              <div
                className="reasoning-header"
                onClick={() => toggle(panel.key)}
              >
                <span className="reasoning-label">{panel.label}</span>
                <span
                  className={`reasoning-expand ${openPanels[panel.key] ? "open" : ""}`}
                >
                  ▼
                </span>
              </div>
              {openPanels[panel.key] && (
                <div className="reasoning-content">{panel.content}</div>
              )}
            </div>
          )
      )}
    </div>
  );
}
