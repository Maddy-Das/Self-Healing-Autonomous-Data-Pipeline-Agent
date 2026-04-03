"use client";
import { useEffect, useRef } from "react";

export default function PipelineDiagram({ mermaidCode }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!mermaidCode || !containerRef.current) return;

    let cancelled = false;

    const renderDiagram = async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          themeVariables: {
            primaryColor: "#6366f1",
            primaryTextColor: "#f1f5f9",
            primaryBorderColor: "#6366f1",
            lineColor: "#8b5cf6",
            secondaryColor: "#1e293b",
            tertiaryColor: "#0f172a",
            fontFamily: "Inter, sans-serif",
          },
        });

        if (cancelled) return;
        const id = "mermaid-" + Date.now();
        const { svg } = await mermaid.render(id, mermaidCode);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = `<pre style="color: var(--text-muted); font-size: 13px;">${mermaidCode}</pre>`;
        }
      }
    };

    renderDiagram();
    return () => { cancelled = true; };
  }, [mermaidCode]);

  if (!mermaidCode) {
    return (
      <div className="glass-card section-panel">
        <div className="section-header">
          <div className="section-title">
            <span className="section-icon">🔀</span> Pipeline Diagram
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-text">
            Pipeline diagram will appear here after generation
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card section-panel">
      <div className="section-header">
        <div className="section-title">
          <span className="section-icon">🔀</span> Pipeline Diagram
        </div>
        <span className="section-badge badge-success">Generated</span>
      </div>
      <div className="mermaid-container" ref={containerRef} />
    </div>
  );
}
