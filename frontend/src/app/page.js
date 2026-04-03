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
      <Header status={status} />

      <main className="main-container">
        {/* Upload Section */}
        <UploadPanel onSubmit={handleSubmit} isLoading={isProcessing} />

        {/* Progress Steps */}
        {status !== "idle" && (
          <div className="progress-steps">
            {STEPS.map((step) => (
              <div
                key={step.key}
                className={`progress-step ${getStepState(step.key)}`}
              >
                <div className="step-circle">
                  {getStepState(step.key) === "done" ? "✓" : step.label[0]}
                </div>
                <div className="step-label">{step.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Error Message */}
        {status === "error" && session?.error_message && (
          <div
            className="glass-card section-panel"
            style={{
              marginTop: 24,
              borderColor: "var(--border-error)",
              background: "rgba(244, 63, 94, 0.05)",
            }}
          >
            <div className="section-title" style={{ color: "var(--accent-rose)" }}>
              <span className="section-icon">❌</span> Error
            </div>
            <p style={{ color: "var(--accent-rose)", marginTop: 12, fontSize: 14 }}>
              {session.error_message}
            </p>
          </div>
        )}

        {/* Dashboard Grid */}
        {session && status !== "idle" && (
          <div className="dashboard-grid">
            {/* Pipeline Diagram - Full Width */}
            <div className="full-width">
              <PipelineDiagram mermaidCode={session.artifacts?.mermaid_diagram} />
            </div>

            {/* Data Quality Report */}
            <div className="full-width">
              <DataQualityReport report={session.quality_report} />
            </div>

            {/* Code Viewer */}
            <CodeViewer artifacts={session.artifacts} />

            {/* Readiness Score */}
            <ReadinessScore readiness={session.readiness} />

            {/* Simulation Results */}
            <SimulationResults result={session.simulation_result} />

            {/* Healing History */}
            <HealingHistory history={session.healing_history} />

            {/* Reasoning Traces - Full Width */}
            <div className="full-width">
              <ReasoningTraces
                builderReasoning={session.builder_reasoning}
                healerReasoning={session.healer_reasoning}
              />
            </div>

            {/* Actions Bar - Full Width */}
            {status === "complete" && (
              <div className="full-width">
                <div className="glass-card section-panel">
                  <div className="section-header">
                    <div className="section-title">
                      <span className="section-icon">⚡</span> Actions
                    </div>
                  </div>

                  <div className="actions-bar">
                    <button
                      className="btn-action btn-download"
                      onClick={handleDownload}
                      id="download-btn"
                    >
                      📦 Download ZIP Package
                    </button>
                    <button
                      className="btn-action btn-heal"
                      onClick={handleHeal}
                      disabled={isHealing}
                      id="heal-btn"
                    >
                      🔧 {isHealing ? "Healing…" : "Run Healing"}
                    </button>
                    <button
                      className="btn-action btn-new"
                      onClick={handleReset}
                      id="reset-btn"
                    >
                      🔄 New Pipeline
                    </button>
                  </div>

                  <div className="heal-input-container">
                    <input
                      className="heal-input"
                      type="text"
                      placeholder="Optional feedback: e.g. 'Fix negative sales values' or 'Add streaming JSON support'"
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
      </main>
    </>
  );
}
