"""
Comprehensive unit tests for the Self-Healing Pipeline Agent backend.
Tests all new enterprise modules: data quality, retry, monitoring, profiler.
"""

import os
import sys
import json
import time
import tempfile
import pytest

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════════════════════
# DATA QUALITY ENGINE TESTS
# ═══════════════════════════════════════════════════════════════

class TestDataQualityEngine:
    """Test all 8 data quality check categories."""

    def test_null_detection_critical(self):
        """Critical alert when nulls > 50%."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 100,
            "duplicate_rows": 0,
            "columns": [{
                "name": "sales",
                "dtype": "float64",
                "semantic_type": "float",
                "null_count": 60,
                "null_percent": 60.0,
                "unique_count": 40,
                "sample_values": ["100.0", "200.0"],
                "min": 0, "max": 1000, "mean": 200, "std": 100,
            }],
        }

        result = run_data_quality_checks(profile)
        critical_checks = [c for c in result["checks"] if c["severity"] == "critical"]
        assert any("60.0% null" in c["description"] for c in critical_checks), \
            "Should flag >50% nulls as critical"

    def test_null_detection_warning(self):
        """Warning when nulls 20-50%."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 100,
            "duplicate_rows": 0,
            "columns": [{
                "name": "city",
                "dtype": "object",
                "semantic_type": "string",
                "null_count": 30,
                "null_percent": 30.0,
                "unique_count": 20,
                "sample_values": ["NYC", "LA"],
            }],
        }

        result = run_data_quality_checks(profile)
        warnings = [c for c in result["checks"] if c["severity"] == "warning"]
        assert any("30.0% null" in c["description"] for c in warnings)

    def test_duplicate_detection(self):
        """Detect high duplicate rate."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 100,
            "duplicate_rows": 15,
            "columns": [],
        }

        result = run_data_quality_checks(profile)
        critical = [c for c in result["checks"] if c["rule"] == "duplicate_threshold"]
        assert len(critical) > 0, "Should detect 15% duplicate rate"
        assert critical[0]["severity"] == "critical"

    def test_pii_detection_email_column(self):
        """Detect PII in column named 'email'."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 100,
            "duplicate_rows": 0,
            "columns": [{
                "name": "email",
                "dtype": "object",
                "semantic_type": "string",
                "null_count": 0,
                "null_percent": 0,
                "unique_count": 100,
                "sample_values": ["test@example.com"],
            }],
        }

        result = run_data_quality_checks(profile)
        assert result["pii_detected"] is True
        assert "email" in result["pii_columns"]

    def test_pii_detection_pattern_match(self):
        """Detect PII via value pattern matching (phone numbers)."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 100,
            "duplicate_rows": 0,
            "columns": [{
                "name": "contact_info",
                "dtype": "object",
                "semantic_type": "string",
                "null_count": 0,
                "null_percent": 0,
                "unique_count": 100,
                "sample_values": ["+1-555-123-4567"],
            }],
        }

        result = run_data_quality_checks(profile)
        assert result["pii_detected"] is True

    def test_outlier_detection(self):
        """Detect statistical outliers."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 1000,
            "duplicate_rows": 0,
            "columns": [{
                "name": "price",
                "dtype": "float64",
                "semantic_type": "float",
                "null_count": 0,
                "null_percent": 0,
                "unique_count": 500,
                "sample_values": ["10.0", "20.0"],
                "min": -100, "max": 100000, "mean": 50, "std": 100,
            }],
        }

        result = run_data_quality_checks(profile)
        outlier_checks = [c for c in result["checks"] if c["rule"] == "outlier_detection"]
        assert len(outlier_checks) > 0

    def test_negative_value_detection(self):
        """Flag negative values in typically-positive columns."""
        from engine.data_quality import run_data_quality_checks

        profile = {
            "row_count": 100,
            "duplicate_rows": 0,
            "columns": [{
                "name": "sales_amount",
                "dtype": "float64",
                "semantic_type": "float",
                "null_count": 0,
                "null_percent": 0,
                "unique_count": 80,
                "sample_values": ["100.0"],
                "min": -50.0, "max": 5000.0, "mean": 200.0, "std": 100.0,
            }],
        }

        result = run_data_quality_checks(profile)
        neg_checks = [c for c in result["checks"] if c["rule"] == "negative_values"]
        assert len(neg_checks) > 0, "Should flag negative sales values"

    def test_schema_drift_detection(self):
        """Detect schema changes between runs."""
        from engine.data_quality import detect_schema_drift

        previous = {
            "columns": [
                {"name": "id", "dtype": "int64", "null_percent": 0},
                {"name": "removed_col", "dtype": "object", "null_percent": 5},
            ]
        }
        current = {
            "columns": [
                {"name": "id", "dtype": "object", "null_percent": 0},  # type changed
                {"name": "new_col", "dtype": "float64", "null_percent": 10},
            ]
        }

        issues = detect_schema_drift(current, previous)
        assert any("removed_col" in i["description"] for i in issues), "Should detect removed column"
        assert any("new_col" in i["description"] for i in issues), "Should detect new column"
        assert any("type changed" in i["description"] for i in issues), "Should detect type change"

    def test_quality_score_calculation(self):
        """Quality score decreases with more issues."""
        from engine.data_quality import run_data_quality_checks

        clean_profile = {
            "row_count": 100,
            "duplicate_rows": 0,
            "columns": [{
                "name": "id",
                "dtype": "int64",
                "semantic_type": "integer",
                "null_count": 0,
                "null_percent": 0,
                "unique_count": 100,
                "sample_values": ["1", "2", "3"],
                "min": 1, "max": 100, "mean": 50, "std": 29,
            }],
        }

        dirty_profile = {
            "row_count": 100,
            "duplicate_rows": 30,
            "columns": [{
                "name": "email",
                "dtype": "object",
                "semantic_type": "string",
                "null_count": 60,
                "null_percent": 60.0,
                "unique_count": 40,
                "sample_values": ["test@example.com"],
            }],
        }

        clean_result = run_data_quality_checks(clean_profile)
        dirty_result = run_data_quality_checks(dirty_profile)

        assert clean_result["quality_score"] > dirty_result["quality_score"], \
            f"Clean ({clean_result['quality_score']}) should score higher than dirty ({dirty_result['quality_score']})"

    def test_pii_masking(self):
        """PII masking produces masked output."""
        from engine.data_quality import mask_pii_value, hash_pii_value

        masked_email = mask_pii_value("john.doe@example.com", "email")
        assert "@" in masked_email
        assert "john.doe" not in masked_email

        hashed = hash_pii_value("john.doe@example.com")
        assert len(hashed) == 16
        assert hashed != "john.doe@example.com"


# ═══════════════════════════════════════════════════════════════
# RETRY ENGINE TESTS
# ═══════════════════════════════════════════════════════════════

class TestRetryEngine:
    """Test retry, circuit breaker, and idempotency."""

    def test_retry_success_on_first_attempt(self):
        """Function succeeds without retry."""
        from engine.retry import retry_with_backoff, RetryConfig

        call_count = 0

        @retry_with_backoff(RetryConfig(max_retries=3, base_delay=0.01))
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = always_succeeds()
        assert result == "ok"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """Function succeeds after some failures."""
        from engine.retry import retry_with_backoff, RetryConfig

        call_count = 0

        @retry_with_backoff(RetryConfig(max_retries=3, base_delay=0.01))
        def fails_then_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temp error")
            return "recovered"

        result = fails_then_succeeds()
        assert result == "recovered"
        assert call_count == 3

    def test_retry_exhaustion(self):
        """All retries exhaust → exception raised."""
        from engine.retry import retry_with_backoff, RetryConfig

        @retry_with_backoff(RetryConfig(max_retries=2, base_delay=0.01))
        def always_fails():
            raise ValueError("permanent error")

        with pytest.raises(ValueError, match="permanent error"):
            always_fails()

    def test_circuit_breaker_trips(self):
        """Circuit breaker opens after threshold failures."""
        from engine.retry import CircuitBreaker, CircuitBreakerOpenError

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0, name="test")
        assert cb.get_state()["state"] == "closed"

        def failing_func():
            raise ValueError("fail")

        # Trip the breaker
        for _ in range(2):
            try:
                cb.call(failing_func)
            except ValueError:
                pass

        assert cb.get_state()["state"] == "open"

        # Should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(failing_func)

    def test_circuit_breaker_recovery(self):
        """Circuit breaker recovers after timeout."""
        from engine.retry import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1, name="test_recovery")

        def failing():
            raise ValueError("fail")

        def succeeding():
            return "ok"

        try:
            cb.call(failing)
        except ValueError:
            pass

        assert cb.get_state()["state"] == "open"

        time.sleep(0.15)  # Wait for recovery timeout
        result = cb.call(succeeding)
        assert result == "ok"
        assert cb.get_state()["state"] == "closed"

    def test_idempotency_checkpointing(self):
        """Checkpoint tracking across stages."""
        from engine.retry import IdempotencyManager

        im = IdempotencyManager("test-idem-session")

        assert im.is_completed("profiling") is False

        im.mark_started("profiling")
        assert im.is_completed("profiling") is False

        im.mark_completed("profiling", metadata={"rows": 100})
        assert im.is_completed("profiling") is True

        progress = im.get_progress()
        assert progress["completed_count"] == 1

        # Cleanup
        if im.checkpoint_file.exists():
            im.checkpoint_file.unlink()

    def test_idempotency_hash(self):
        """Deterministic hash for same input."""
        from engine.retry import IdempotencyManager

        hash1 = IdempotencyManager.compute_hash("hello world")
        hash2 = IdempotencyManager.compute_hash("hello world")
        hash3 = IdempotencyManager.compute_hash("different")

        assert hash1 == hash2
        assert hash1 != hash3

    def test_watermark_manager(self):
        """Watermark persistence and retrieval."""
        from engine.retry import WatermarkManager

        wm = WatermarkManager("test-wm-session")
        wm.set_watermark("sales_csv", "2024-01-15T00:00:00Z")

        assert wm.get_watermark("sales_csv") == "2024-01-15T00:00:00Z"
        assert wm.get_watermark("nonexistent") == ""

        # Cleanup
        if wm.watermark_file.exists():
            wm.watermark_file.unlink()


# ═══════════════════════════════════════════════════════════════
# MONITORING MODULE TESTS
# ═══════════════════════════════════════════════════════════════

class TestMonitoring:
    """Test structured logging, metrics, and lineage."""

    def test_metrics_recording(self):
        """Record and retrieve metrics."""
        from engine.monitoring import MetricsCollector

        mc = MetricsCollector()
        mc.record("test_metric", 42.0, {"session_id": "s1"})
        mc.record("test_metric", 43.0, {"session_id": "s1"})

        summary = mc.get_summary()
        assert summary["total_metrics"] >= 2

    def test_timer(self):
        """Start/stop timer produces positive duration."""
        from engine.monitoring import MetricsCollector

        mc = MetricsCollector()
        mc.start_timer("test_phase", "s2")
        time.sleep(0.05)
        duration = mc.stop_timer("test_phase", "s2")

        assert duration > 0, f"Duration should be positive, got {duration}"

    def test_event_recording(self):
        """Record pipeline lifecycle events."""
        from engine.monitoring import MetricsCollector

        mc = MetricsCollector()
        mc.record_event("pipeline_created", "s3", {"filename": "test.csv"})

        session_metrics = mc.get_session_metrics("s3")
        assert len(session_metrics["events"]) >= 1
        assert session_metrics["events"][0]["event_type"] == "pipeline_created"

    def test_lineage_tracker(self):
        """Track source → transform → sink lineage."""
        from engine.monitoring import LineageTracker

        lt = LineageTracker("s4")
        lt.record_source("sales.csv", "csv", {"rows": 1000})
        lt.record_transformation("clean_nulls", 1000, 950)
        lt.record_sink("sales_table", "sqlite", 950)

        lineage = lt.get_lineage()
        assert len(lineage) == 3
        assert lineage[0]["type"] == "source"
        assert lineage[1]["type"] == "transformation"
        assert lineage[2]["type"] == "sink"

    def test_lineage_mermaid_output(self):
        """Lineage generates valid Mermaid diagram."""
        from engine.monitoring import LineageTracker

        lt = LineageTracker("s5")
        lt.record_source("input.csv", "csv")
        lt.record_transformation("etl", 100, 95)
        lt.record_sink("output_table", "db", 95)

        mermaid = lt.get_mermaid()
        assert "graph LR" in mermaid
        assert "input.csv" in mermaid


# ═══════════════════════════════════════════════════════════════
# PROFILER TESTS
# ═══════════════════════════════════════════════════════════════

class TestProfiler:
    """Test CSV profiling."""

    def test_profile_csv(self):
        """Profile a simple CSV file."""
        from engine.profiler import profile_csv

        # Create temp CSV
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,name,amount,date\n")
            f.write("1,Alice,100.50,2024-01-01\n")
            f.write("2,Bob,200.75,2024-01-02\n")
            f.write("3,Alice,100.50,2024-01-01\n")  # duplicate
            f.write("4,,150.00,2024-01-04\n")  # null name
            csv_path = f.name

        try:
            profile = profile_csv(csv_path)

            assert profile["row_count"] == 4
            assert profile["column_count"] == 4
            assert profile["duplicate_rows"] >= 0

            # Check column profiling
            name_col = next(c for c in profile["columns"] if c["name"] == "name")
            assert name_col["null_count"] == 1
            assert name_col["null_percent"] == 25.0

            amount_col = next(c for c in profile["columns"] if c["name"] == "amount")
            assert amount_col["semantic_type"] == "float"
        finally:
            os.unlink(csv_path)


# ═══════════════════════════════════════════════════════════════
# SIMULATOR TESTS
# ═══════════════════════════════════════════════════════════════

class TestSimulator:
    """Test 3-layer simulation engine."""

    def test_etl_simulation_basic(self):
        """Basic ETL code runs in sandbox."""
        from engine.simulator import run_etl_simulation

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("x,y\n1,10\n2,20\n3,30\n")
            csv_path = f.name

        try:
            code = """
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} rows")
df['z'] = df['x'] + df['y']

conn = sqlite3.connect(db_path)
df.to_sql('result', conn, if_exists='replace', index=False)
conn.close()
print("Done!")
"""
            result = run_etl_simulation(code, csv_path)
            assert result["success"] is True
            assert result["input_rows"] == 3
            assert result["output_rows"] >= 3
        finally:
            os.unlink(csv_path)

    def test_etl_simulation_error(self):
        """ETL code with error is caught."""
        from engine.simulator import run_etl_simulation

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("a,b\n1,2\n")
            csv_path = f.name

        try:
            code = "raise ValueError('test error')"
            result = run_etl_simulation(code, csv_path)
            assert result["success"] is False
            assert len(result["errors"]) > 0
        finally:
            os.unlink(csv_path)

    def test_dag_validation_complete(self):
        """Validate a complete DAG structure."""
        from engine.simulator import validate_dag

        dag_code = '''
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {"retries": 3, "retry_delay": timedelta(minutes=5)}

with DAG("my_pipeline", schedule_interval="@daily", start_date=datetime(2024, 1, 1), default_args=default_args) as dag:
    t1 = PythonOperator(task_id="extract", python_callable=lambda: None)
    t2 = PythonOperator(task_id="transform", python_callable=lambda: None)
    t3 = PythonOperator(task_id="load", python_callable=lambda: None)
    t1 >> t2 >> t3
'''
        result = validate_dag(dag_code)
        assert result["valid_syntax"] is True
        assert result["has_dag_definition"] is True
        assert result["has_tasks"] is True
        assert result["task_count"] >= 3

    def test_sql_validation(self):
        """Validate SQL schema execution."""
        from engine.simulator import validate_sql

        ddl = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
        result = validate_sql(ddl)
        assert result["schema_valid"] is True
        assert "users" in result["tables_created"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
