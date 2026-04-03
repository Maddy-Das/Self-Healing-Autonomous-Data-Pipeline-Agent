"""
Structured Logging & Monitoring Module
Production-grade structured logging with JSON output, metrics collection,
and alerting hooks. Covers: latency tracking, row counts, error rates,
pipeline stage timing, and data lineage events.
"""

import json
import time
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps
from config import BASE_DIR

# ── Log Directory ───────────────────────────────────────────────
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """JSON-formatted log entries for production observability."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        for key in ("session_id", "phase", "duration_ms", "row_count",
                     "error_type", "iteration", "metric_name", "metric_value",
                     "component", "event_type"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Create a structured logger with console + file outputs."""
    logger = logging.getLogger(f"pipeline.{name}")

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Console handler (structured JSON)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(StructuredFormatter())

        # File handler (all levels)
        file_handler = logging.FileHandler(LOG_DIR / "pipeline.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# ── Metrics Collector ───────────────────────────────────────────

class MetricsCollector:
    """
    In-memory metrics collector for pipeline observability.
    Tracks latency, row counts, error rates, and custom metrics.
    In production, this would push to Prometheus/Grafana/Datadog.
    """

    def __init__(self):
        self.metrics = {}
        self.timers = {}
        self.events = []
        self.logger = get_logger("metrics")

    def record(self, name: str, value: float, labels: dict = None):
        """Record a metric value."""
        key = name
        if labels:
            key += ":" + ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append({
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "labels": labels or {},
        })

        self.logger.info(
            f"Metric: {name}={value}",
            extra={"metric_name": name, "metric_value": value, "component": "metrics"},
        )

    def start_timer(self, name: str, session_id: str = ""):
        """Start a named timer."""
        key = f"{name}:{session_id}"
        self.timers[key] = time.time()

    def stop_timer(self, name: str, session_id: str = "") -> float:
        """Stop a named timer and record the duration."""
        key = f"{name}:{session_id}"
        if key in self.timers:
            duration_ms = (time.time() - self.timers[key]) * 1000
            self.record(f"{name}_duration_ms", duration_ms, {"session_id": session_id})
            del self.timers[key]
            return duration_ms
        return 0

    def record_event(self, event_type: str, session_id: str, details: dict = None):
        """Record a pipeline lifecycle event for lineage tracking."""
        event = {
            "event_type": event_type,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
        self.events.append(event)
        self.logger.info(
            f"Event: {event_type}",
            extra={"event_type": event_type, "session_id": session_id, "component": "lineage"},
        )

    def get_session_metrics(self, session_id: str) -> dict:
        """Get all metrics for a specific session."""
        session_metrics = {}
        for key, values in self.metrics.items():
            session_values = [v for v in values if v.get("labels", {}).get("session_id") == session_id]
            if session_values:
                session_metrics[key.split(":")[0]] = session_values

        session_events = [e for e in self.events if e.get("session_id") == session_id]

        return {
            "metrics": session_metrics,
            "events": session_events,
        }

    def get_summary(self) -> dict:
        """Get overall metrics summary."""
        return {
            "total_metrics": sum(len(v) for v in self.metrics.values()),
            "total_events": len(self.events),
            "metric_keys": list(set(k.split(":")[0] for k in self.metrics.keys())),
            "event_types": list(set(e["event_type"] for e in self.events)),
        }


# ── Global Metrics Instance ────────────────────────────────────
metrics = MetricsCollector()


# ── Decorators ──────────────────────────────────────────────────

def track_duration(phase_name: str):
    """Decorator to track execution duration of pipeline phases."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(phase_name)
            session_id = kwargs.get("session_id", args[0] if args else "unknown")

            logger.info(
                f"Starting {phase_name}",
                extra={"phase": phase_name, "session_id": session_id},
            )
            metrics.start_timer(phase_name, str(session_id))

            try:
                result = func(*args, **kwargs)

                duration = metrics.stop_timer(phase_name, str(session_id))
                logger.info(
                    f"Completed {phase_name} in {duration:.0f}ms",
                    extra={"phase": phase_name, "session_id": session_id, "duration_ms": duration},
                )
                return result

            except Exception as e:
                duration = metrics.stop_timer(phase_name, str(session_id))
                logger.error(
                    f"Failed {phase_name}: {str(e)}",
                    extra={
                        "phase": phase_name, "session_id": session_id,
                        "duration_ms": duration, "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                metrics.record("errors_total", 1, {"phase": phase_name, "session_id": str(session_id)})
                raise

        return wrapper
    return decorator


# ── Data Lineage Tracker ────────────────────────────────────────

class LineageTracker:
    """
    Track data lineage through the pipeline.
    In production, this would integrate with OpenLineage / Marquez.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.lineage = []
        self.logger = get_logger("lineage")

    def record_source(self, source_name: str, source_type: str, details: dict = None):
        self.lineage.append({
            "type": "source",
            "name": source_name,
            "source_type": source_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        })
        metrics.record_event("data_source_read", self.session_id, {"source": source_name})

    def record_transformation(self, transform_name: str, input_rows: int, output_rows: int, details: dict = None):
        self.lineage.append({
            "type": "transformation",
            "name": transform_name,
            "input_rows": input_rows,
            "output_rows": output_rows,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        })
        metrics.record("transform_row_delta", output_rows - input_rows, {"transform": transform_name})

    def record_sink(self, sink_name: str, sink_type: str, row_count: int, details: dict = None):
        self.lineage.append({
            "type": "sink",
            "name": sink_name,
            "sink_type": sink_type,
            "row_count": row_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        })
        metrics.record_event("data_sink_write", self.session_id, {"sink": sink_name, "rows": row_count})

    def get_lineage(self) -> list:
        return self.lineage

    def get_mermaid(self) -> str:
        """Generate a Mermaid lineage diagram."""
        lines = ["graph LR"]
        for i, node in enumerate(self.lineage):
            node_id = f"N{i}"
            label = node["name"]
            if node["type"] == "source":
                lines.append(f'    {node_id}[("{label}")]')
            elif node["type"] == "transformation":
                lines.append(f'    {node_id}["{label}\\n{node.get("input_rows", "?")}→{node.get("output_rows", "?")} rows"]')
            elif node["type"] == "sink":
                lines.append(f'    {node_id}[("{label}\\n{node.get("row_count", "?")} rows")]')

            if i > 0:
                lines.append(f"    N{i-1} --> {node_id}")

        return "\n".join(lines)
