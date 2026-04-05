"use client";
import { useState, useRef, useCallback, useEffect } from "react";
import Header from "@/components/Header";
import UploadPanel from "@/components/UploadPanel";
import PipelineDiagram from "@/components/PipelineDiagram";
import CodeViewer from "@/components/CodeViewer";
import ReasoningTraces from "@/components/ReasoningTraces";
import SimulationResults from "@/components/SimulationResults";
import HealingHistory from "@/components/HealingHistory";
import ReadinessScore from "@/components/ReadinessScore";
import DataQualityReport from "@/components/DataQualityReport";

const API = "http://localhost:8000";

const STEPS = [
  { key: "profiling", label: "Profile" },
  { key: "generating", label: "Generate" },
  { key: "simulating", label: "Simulate" },
  { key: "healing", label: "Heal" },
  { key: "complete", label: "Done" },
];

const stepOrder = STEPS.map((s) => s.key);

export default function Home() {
  const [status, setStatus] = useState("idle");
  const [session, setSession] = useState(null);
  const [healFeedback, setHealFeedback] = useState("");
  const [isHealing, setIsHealing] = useState(false);
  const pollRef = useRef(null);

  const pollStatus = useCallback((sessionId) => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API}/api/pipeline/${sessionId}/status`);
        const data = await res.json();
        setSession(data);
        setStatus(data.status);

        if (data.status === "complete" || data.status === "error") {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch {
        // Backend might not be ready yet, keep polling
      }
    }, 2000);
  }, []);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleSubmit = async (file, prompt) => {
    setStatus("profiling");
    setSession(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("prompt", prompt);

    try {
      const res = await fetch(`${API}/api/pipeline/create`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      pollStatus(data.session_id);
    } catch (err) {
      setStatus("error");
      setSession({ error_message: "Failed to connect to backend: " + err.message });
    }
  };

  const handleHeal = async () => {
    if (!session?.session_id) return;
    setIsHealing(true);
    setStatus("healing");

    const formData = new FormData();
    formData.append("feedback", healFeedback || "");

    try {
      await fetch(`${API}/api/pipeline/${session.session_id}/heal`, {
        method: "POST",
        body: formData,
      });
      // Re-poll for latest state
      const res = await fetch(`${API}/api/pipeline/${session.session_id}/status`);
      const data = await res.json();
      setSession(data);
      setStatus(data.status);
    } catch (err) {
      setStatus("error");
    } finally {
      setIsHealing(false);
      setHealFeedback("");
    }
  };

  const handleDownload = () => {
    if (session?.session_id) {
      window.open(`${API}/api/pipeline/${session.session_id}/download`, "_blank");
    }
  };

  const handleReset = () => {
    setStatus("idle");
    setSession(null);
    setHealFeedback("");
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const getStepState = (stepKey) => {
    const currentIdx = stepOrder.indexOf(status);
    const stepIdx = stepOrder.indexOf(stepKey);
    if (stepIdx < 0) return "";
    if (status === "idle" || status === "error") return "";
    if (stepIdx < currentIdx) return "done";
    if (stepIdx === currentIdx) return "active";
    return "";
  };

  const isProcessing = ["profiling", "generating", "simulating", "healing"].includes(status);

  return (
    <>
    <div className="app-container">

      {/* Sidebar Navigation */}
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <img src="/logo.png" alt="Aura Logo" className="brand-icon aura-logo-animate" style={{ background: '#ffffff', borderRadius: '4px', objectFit: 'contain', padding: '4px', border: '1px solid var(--border-subtle)' }} />
          <div className="brand-name">AuraPipeline</div>
        </div>

        <nav className="nav-section">
          <div className={`nav-item ${status === 'idle' ? 'active' : ''}`}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
            Overview
          </div>
          <div className={`nav-item ${status !== 'idle' ? 'active' : ''}`}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            Architecture
          </div>
        </nav>

        {status !== "idle" && (
          <div className="progress-section" style={{ marginTop: '24px' }}>
            <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
              Execution Lifecycle
            </div>
            <div className="progress-list">
              {STEPS.map((step) => {
                const s = getStepState(step.key);
                return (
                  <div key={step.key} className={`progress-item ${s}`}>
                    <div className="status-dot" />
                    {step.label}
                    {s === 'done' && <span style={{ marginLeft: 'auto', fontSize: '10px' }}>✓</span>}
                  </div>
                );
              })}
            </div>
            {session?.current_action && status !== 'complete' && status !== 'error' && (
              <div 
                className="current-action-peek shimmer-bg" 
                style={{ 
                  marginTop: '16px', fontSize: '11px', color: 'var(--brand-primary)', 
                  fontStyle: 'italic', padding: '10px', background: 'rgba(79, 70, 229, 0.03)',
                  borderRadius: '6px', borderLeft: '2px solid var(--brand-primary)',
                  animation: 'fadeIn 0.5s'
                }}
              >
                {session.current_action}
              </div>
            )}
          </div>
        )}

        <div className="sidebar-status" style={{ marginTop: 'auto' }}>
          <div style={{ fontSize: '11px', fontWeight: '800', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>System Status</div>
          <Header status={status} />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-viewport custom-scroll">
        <div className="viewport-content">
          
          {/* Upload Area */}
          <div className="animate-stagger-1">
            <UploadPanel onSubmit={handleSubmit} isLoading={isProcessing} />
          </div>

          {/* System Error Notification */}
          {status === "error" && session?.error_message && (
            <div className="glass-card section-panel animate-stagger-2" style={{ border: '1px solid var(--brand-error)', background: '#fff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--brand-error)', fontWeight: '700', fontSize: '14px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Execution Fault
              </div>
              <p style={{ color: "var(--text-secondary)", marginTop: '12px', fontSize: '13px', lineHeight: '1.6' }}>
                The synthesis engine encountered a critical architectural boundary: <code style={{ color: 'var(--brand-error)', background: 'rgba(239, 68, 68, 0.05)', padding: '2px 4px', borderRadius: '4px' }}>{session.error_message}</code>
              </p>
            </div>
          )}

          {/* Core Synthesis Workspace */}
          {session && status !== "idle" && (
            <div className="dashboard-grid">
              
              {/* Architecture Blueprint */}
              <div className="full-width animate-stagger-2">
                <PipelineDiagram mermaidCode={session.artifacts?.mermaid_diagram} />
              </div>

              {/* Integrity Assessment */}
              <div className="full-width animate-stagger-3">
                <DataQualityReport report={session.quality_report} />
              </div>

              {/* Logic Implementation */}
              <div className="animate-stagger-4">
                <CodeViewer artifacts={session.artifacts} />
              </div>

              {/* Deployment Certification */}
              <div className="animate-stagger-5">
                <ReadinessScore readiness={session.readiness} />
              </div>

              {/* Verification Logs */}
              <SimulationResults result={session.simulation_result} />

              {/* Delta Resolution History */}
              <HealingHistory history={session.healing_history} />

              {/* Agentic Reasoning Traces */}
              <div className="full-width">
                <ReasoningTraces
                  builderReasoning={session.builder_reasoning}
                  healerReasoning={session.healer_reasoning}
                />
              </div>

              {/* Control Interface */}
              {status === "complete" && (
                <div className="full-width">
                  <div className="glass-card section-panel">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px', fontWeight: '700', fontSize: '14px', color: 'var(--text-primary)' }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                      Integration Workflow
                    </div>

                    <div className="actions-bar" style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
                      <button className="btn-action btn-download" onClick={handleDownload} id="download-btn">Export Artifacts</button>
                      <button className="btn-action btn" onClick={handleHeal} disabled={isHealing} id="heal-btn" style={{ fontWeight: '600' }}>
                        {isHealing ? "Resolving..." : "Repair Sequence"}
                      </button>
                      <button className="btn-action btn" onClick={handleReset} id="reset-btn" style={{ marginLeft: 'auto', fontWeight: '600' }}>Reset Architecture</button>
                    </div>

                    <div className="heal-input-container">
                      <input
                        className="heal-input"
                        type="text"
                        placeholder="Architectural constraints or feedback..."
                        value={healFeedback}
                        onChange={(e) => setHealFeedback(e.target.value)}
                        id="heal-feedback"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>


    </>
  );
}
