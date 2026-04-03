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
    <div className="glass-card upload-panel">
      <div className="upload-inner">
        <h2 className="upload-title">Build Your Pipeline</h2>
        <p className="upload-desc">
          Upload a CSV dataset and describe the pipeline you need in plain
          English. The AI agent will build, simulate, and self-heal it
          automatically.
        </p>

        <div
          className={`dropzone ${dragActive ? "active" : ""}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          id="csv-dropzone"
        >
          <div className="dropzone-icon">📁</div>
          <div className="dropzone-text">
            <strong>Click to upload</strong> or drag and drop your CSV file
            <br />
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Supports .csv files up to 50MB
            </span>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: "none" }}
            id="csv-file-input"
          />
        </div>

        {file && (
          <div className="file-info">
            <span className="file-info-icon">✅</span>
            <div>
              <div className="file-info-name">{file.name}</div>
              <div className="file-info-size">{formatSize(file.size)}</div>
            </div>
          </div>
        )}

        <div className="prompt-area">
          <label className="prompt-label" htmlFor="pipeline-prompt">
            🎯 Describe Your Pipeline
          </label>
          <textarea
            id="pipeline-prompt"
            className="prompt-input"
            placeholder='Example: "Ingest daily sales data → clean duplicates & nulls → calculate total revenue per region → flag anomalies where revenue drops >30% → store results in PostgreSQL → schedule daily at 8 AM"'
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
        >
          {isLoading ? "Generating…" : "🚀 Generate Pipeline"}
        </button>
      </div>
    </div>
  );
}
