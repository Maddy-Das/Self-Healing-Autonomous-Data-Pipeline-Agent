"use client";
import { useRef, useState } from "react";

export default function UploadPanel({ onSubmit, isLoading }) {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) setFile(e.target.files[0]);
  };

  const handleSubmit = () => {
    if (file && prompt.trim()) {
      onSubmit(file, prompt.trim());
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="upload-panel" style={{ borderBottom: '1px solid var(--border-subtle)', background: 'transparent', paddingBottom: '60px' }}>
      <div className="upload-inner">
        <h1 className="upload-title" style={{ fontSize: '32px', fontWeight: '800', marginBottom: '8px' }}>Execute Synthesis</h1>
        <p className="upload-desc" style={{ fontSize: '15px', color: 'var(--text-secondary)', marginBottom: '40px' }}>
          Deploy an autonomous agent to architect and self-heal your data infrastructure from source.
        </p>

        <div
          className={`dropzone ${dragActive ? "active" : ""}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          id="csv-dropzone"
          style={{ 
            borderColor: dragActive ? 'var(--brand-primary)' : 'var(--border-strong)',
            background: dragActive ? '#f8fafc' : 'var(--bg-sidebar)',
            padding: '48px', borderRadius: '12px'
          }}
        >
          <div className="dropzone-icon" style={{ 
            width: '48px', height: '48px', margin: '0 auto 16px',
            borderRadius: '8px', background: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--brand-primary)', border: '1px solid var(--border-strong)'
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          </div>
          <div style={{ fontSize: '14px', fontWeight: '600' }}>
            {file ? file.name : "Select source dataset or drag-and-drop CSV"}
            {!file && <div style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: "400", marginTop: '4px' }}>Standard CSV format · Max 50MB</div>}
          </div>
          {file && <div style={{ fontSize: '11px', color: 'var(--brand-success)', marginTop: '4px', fontWeight: '800' }}>READY FOR SYNTHESIS · {formatSize(file.size)}</div>}
          <input ref={fileRef} type="file" accept=".csv" onChange={handleFileChange} style={{ display: "none" }} id="csv-file-input" />
        </div>

        <div className="prompt-area" style={{ marginTop: '32px', textAlign: 'left' }}>
          <label style={{ 
            fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', 
            color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '8px',
            display: 'block'
          }}>
            Architecture Specification
          </label>
          <textarea
            id="pipeline-prompt"
            className="prompt-input"
            style={{ 
              width: '100%', height: '100px', borderRadius: '8px',
              padding: '16px', fontSize: '14px', background: '#fff'
            }}
            placeholder='Ex: "Standardize ROI calculation, redact PII from source, and synthesize optimized Snowflake schema"'
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <button
          className={`btn-generate ${isLoading ? "loading" : ""}`}
          onClick={handleSubmit}
          disabled={!file || !prompt.trim() || isLoading}
          id="generate-btn"
          style={{ 
            marginTop: '24px', width: '100%', height: '48px', borderRadius: '8px',
            background: 'var(--brand-primary)', fontWeight: '700', 
            fontSize: '14px', border: 'none', color: '#fff',
            cursor: (file && prompt.trim() && !isLoading) ? 'pointer' : 'not-allowed',
            opacity: (file && prompt.trim() && !isLoading) ? 1 : 0.6
          }}
        >
          {isLoading ? "Synthesizing Core Artifacts..." : "Execute Infrastructure Synthesis"}
        </button>
      </div>
    </div>
  );
}
