"use client";
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

export default function PipelineDiagram({ mermaidCode }) {
  const containerRef = useRef(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "loose",
      themeVariables: {
        primaryColor: "#4f46e5",
        primaryTextColor: "#0f172a",
        lineColor: "#334155",
        secondaryColor: "#f1f5f9",
        tertiaryColor: "#ffffff",
        fontFamily: "Inter, -apple-system, sans-serif"
      },
    });
  }, []);

  useEffect(() => {
    if (mermaidCode && containerRef.current) {
      mermaid.contentLoaded();
      const renderDiagram = async () => {
        try {
          const { svg } = await mermaid.render(`diagram-${Date.now()}`, mermaidCode);
          if (containerRef.current) {
             containerRef.current.innerHTML = svg;
          }
        } catch (err) {
          console.error("Mermaid error:", err);
          if (containerRef.current) {
            containerRef.current.innerText = "Architecture Blueprint Synthesis Pending Artifacts...";
          }
        }
      };
      renderDiagram();
    }
  }, [mermaidCode]);

  if (!mermaidCode) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1px solid var(--border-subtle)', background: 'transparent' }}>
          <div className="section-title">Architecture Blueprint</div>
        </div>
        <div className="empty-state">
          <div className="empty-state-text" style={{ fontSize: '13px', opacity: 0.5 }}>
            Synthesized system architecture will be available post-synthesis.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header" style={{ padding: '0px', height: '48px', borderBottom: '1.5px solid var(--border-subtle)', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="section-title">Architecture Blueprint</div>
        <div className="section-badge badge-info" style={{ fontSize: '10px' }}>SYSTEM MANIFEST</div>
      </div>
      <div
        ref={containerRef}
        className="mermaid-container"
        style={{ width: "100%", textAlign: "center", marginTop: "32px", overflowX: "auto", background: 'transparent', padding: '24px 0' }}
      >
        {/* Mermaid SVG renders here */}
      </div>
    </div>
  );
}
