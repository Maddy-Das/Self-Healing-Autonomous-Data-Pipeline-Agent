"""
Retry & Resilience Engine
Implements exponential backoff, circuit breaker pattern, and idempotent
execution strategies for fault-tolerant pipeline operations.
"""

import time
import random
import hashlib
import json
import logging
from functools import wraps
from datetime import datetime, timezone
from pathlib import Path
from config import BASE_DIR
from engine.monitoring import get_logger, metrics

logger = get_logger("retry")

# ── Checkpoint Store ────────────────────────────────────────────
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
CHECKPOINT_DIR.mkdir(exist_ok=True)


class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


def retry_with_backoff(config: RetryConfig = None):
    """
    Decorator: Retry a function with exponential backoff.

    Implements the production pattern used by Netflix/Uber:
    delay = min(max_delay, base_delay * (exponential_base ^ attempt)) + random_jitter
    """
    if config is None:
        config = RetryConfig()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Succeeded after {attempt} retries: {func.__name__}",
                            extra={"iteration": attempt, "component": "retry"},
                        )
                        metrics.record("retry_success", 1, {"function": func.__name__, "attempts": str(attempt)})
                    return result

                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = min(
                            config.max_delay,
                            config.base_delay * (config.exponential_base ** attempt),
                        )
                        if config.jitter:
                            delay += random.uniform(0, delay * 0.1)

                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} for {func.__name__}: {str(e)}. "
                            f"Waiting {delay:.1f}s",
                            extra={
                                "iteration": attempt + 1,
                                "error_type": type(e).__name__,
                                "component": "retry",
                            },
                        )
                        metrics.record("retry_attempt", 1, {"function": func.__name__})
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries} retries exhausted for {func.__name__}: {str(e)}",
                            extra={"error_type": type(e).__name__, "component": "retry"},
                        )
                        metrics.record("retry_exhausted", 1, {"function": func.__name__})

            raise last_exception

        return wrapper
    return decorator


# ── Circuit Breaker ─────────────────────────────────────────────

class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.
    States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing recovery)
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0, name: str = "default"):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.logger = get_logger(f"circuit_breaker.{name}")

    def call(self, func, *args, **kwargs):
        """Execute a function through the circuit breaker."""
        if self.state == self.OPEN:
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = self.HALF_OPEN
                self.logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN — blocking calls for {self.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)

            if self.state == self.HALF_OPEN:
                self.state = self.CLOSED
                self.failure_count = 0
                self.logger.info(f"Circuit breaker '{self.name}' recovered → CLOSED")

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN
                self.logger.error(
                    f"Circuit breaker '{self.name}' tripped → OPEN after {self.failure_count} failures"
                )
                metrics.record("circuit_breaker_trip", 1, {"breaker": self.name})

            raise

    def get_state(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
        }


class CircuitBreakerOpenError(Exception):
    pass


# ── Idempotency Manager ────────────────────────────────────────

class IdempotencyManager:
    """
    Ensures pipeline operations are idempotent.
    Uses checkpointing to track completed stages and prevent duplicate processing.
    Implements MERGE/UPSERT strategies for database writes.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.checkpoint_file = CHECKPOINT_DIR / f"{session_id}.json"
        self.checkpoints = self._load_checkpoints()
        self.logger = get_logger("idempotency")

    def _load_checkpoints(self) -> dict:
        if self.checkpoint_file.exists():
            try:
                return json.loads(self.checkpoint_file.read_text())
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_checkpoints(self):
        self.checkpoint_file.write_text(json.dumps(self.checkpoints, indent=2, default=str))

    def is_completed(self, stage: str) -> bool:
        """Check if a pipeline stage has already been completed."""
        return self.checkpoints.get(stage, {}).get("status") == "completed"

    def mark_started(self, stage: str, input_hash: str = ""):
        """Mark a stage as started."""
        self.checkpoints[stage] = {
            "status": "started",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "input_hash": input_hash,
        }
        self._save_checkpoints()
        self.logger.info(f"Stage '{stage}' started", extra={"phase": stage, "session_id": self.session_id})

    def mark_completed(self, stage: str, output_hash: str = "", metadata: dict = None):
        """Mark a stage as completed with optional output hash for verification."""
        self.checkpoints[stage] = {
            "status": "completed",
            "started_at": self.checkpoints.get(stage, {}).get("started_at"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "output_hash": output_hash,
            "metadata": metadata or {},
        }
        self._save_checkpoints()
        self.logger.info(f"Stage '{stage}' completed", extra={"phase": stage, "session_id": self.session_id})

    def mark_failed(self, stage: str, error: str):
        """Mark a stage as failed."""
        self.checkpoints[stage] = {
            "status": "failed",
            "started_at": self.checkpoints.get(stage, {}).get("started_at"),
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }
        self._save_checkpoints()

    def get_progress(self) -> dict:
        """Get checkpoint progress summary."""
        return {
            "session_id": self.session_id,
            "stages": self.checkpoints,
            "completed_count": sum(1 for v in self.checkpoints.values() if v.get("status") == "completed"),
            "total_stages": len(self.checkpoints),
        }

    @staticmethod
    def compute_hash(data: str) -> str:
        """Compute a deterministic hash of data for idempotency checks."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# ── Watermark Manager ──────────────────────────────────────────

class WatermarkManager:
    """
    Manages high-water marks for incremental processing.
    Tracks the last processed timestamp/offset per source.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.watermark_file = CHECKPOINT_DIR / f"{session_id}_watermarks.json"
        self.watermarks = self._load()

    def _load(self) -> dict:
        if self.watermark_file.exists():
            try:
                return json.loads(self.watermark_file.read_text())
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save(self):
        self.watermark_file.write_text(json.dumps(self.watermarks, indent=2, default=str))

    def get_watermark(self, source: str) -> str:
        """Get the high-water mark for a source."""
        return self.watermarks.get(source, {}).get("value", "")

    def set_watermark(self, source: str, value: str):
        """Update the high-water mark for a source."""
        self.watermarks[source] = {
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def get_all(self) -> dict:
        return self.watermarks
