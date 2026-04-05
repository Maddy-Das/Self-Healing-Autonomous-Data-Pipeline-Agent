"""
Enterprise-Grade Builder Agent
Uses GLM 5.1 to generate production-ready data pipeline code.
Incorporates: idempotency, retry logic, PII handling, schema drift detection,
incremental processing, and comprehensive error handling.
"""

import json
import re
from zhipuai import ZhipuAI
from config import ZHIPUAI_API_KEY, GLM_MODEL
from engine.monitoring import get_logger, metrics
from engine.retry import retry_with_backoff, RetryConfig, CircuitBreaker

logger = get_logger("builder_agent")

# Circuit breaker for LLM API calls
llm_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0, name="glm_builder")

client = ZhipuAI(
    api_key=ZHIPUAI_API_KEY,
    base_url="https://api.z.ai/api/coding/paas/v4"
)

BUILDER_SYSTEM_PROMPT = """You are a Senior Data Pipeline Architect building PRODUCTION-READY pipelines.
Design like Netflix, Uber, or Amazon — not toy scripts.

You MUST respond with a SINGLE valid JSON object containing these exact keys:
{
  "etl_code": "Complete Python ETL script (details below)",
  "sql_schema": "PostgreSQL DDL with constraints, indexes, and partitioning",
  "airflow_dag": "Complete Airflow DAG with error handling and SLAs",
  "mermaid_diagram": "Mermaid flowchart showing complete data lineage",
  "reasoning": "Step-by-step architectural decisions and trade-offs"
}

## ETL CODE REQUIREMENTS (critical):
The ETL script MUST:
1. Read CSV from variable `csv_path` (pre-defined in sandbox)
2. Write results to SQLite database at variable `db_path` (pre-defined)
3. Use ONLY: pandas (as pd), sqlite3, datetime — already imported in sandbox
4. **CRITICAL**: Write COMPLETE, runnable import statements. NEVER write partial imports like 'import sq' - always write 'import sqlite3'
5. Print progress messages using print()
6. Implement these PRODUCTION patterns:
   - **Idempotent writes**: Use INSERT OR REPLACE / UPSERT to prevent duplicates on re-run
   - **Null handling**: Explicit strategy for each column (fill, drop, or flag)
   - **Type casting**: Safe conversion with error handling
   - **Deduplication**: Remove exact duplicates early in pipeline
   - **Data validation**: Assert row counts, check critical columns not empty
   - **Error handling**: try/except with meaningful error messages
   - **Logging**: print() statements showing row counts at each transformation step
   - **Anomaly flagging**: Flag outlier values in a separate column where appropriate
   - **PII awareness**: If columns look like PII, add a comment noting they should be masked

## SQL SCHEMA REQUIREMENTS:
- PostgreSQL-compatible DDL
- Proper data types, NOT NULL constraints, DEFAULT values
- Primary keys and indexes for query performance
- Created_at / updated_at timestamp columns
- Table and column comments

## AIRFLOW DAG REQUIREMENTS:
- Proper imports and DAG definition
- Tasks with meaningful names and descriptions
- Task dependencies using >>
- schedule_interval set appropriately
- retries=3 with retry_delay=timedelta(minutes=5)
- on_failure_callback for alerting
- SLA definitions
- Tags for organization

## MERMAID DIAGRAM:
- Show source → ingestion → transformations → quality checks → destination
- Include data volume annotations where relevant

CRITICAL RULES:
1. Return ONLY the JSON object — no markdown formatting before or after.
2. DO NOT USE MARKDOWN CODE BLOCKS (```python) INSIDE THE JSON VALUES. The code should just be a raw string with \\n for newlines.
3. Code must be self-contained."""


@retry_with_backoff(RetryConfig(max_retries=2, base_delay=2.0))
def _call_llm(messages: list) -> str:
    """Call GLM API with retry and circuit breaker protection."""
    def make_call():
        response = client.chat.completions.create(
            model=GLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=16000,  # Increased from 8000 to accommodate all artifacts
        )
        return response.choices[0].message.content.strip()

    return llm_breaker.call(make_call)


def generate_pipeline(prompt: str, data_profile: dict, quality_report: dict = None) -> dict:
    """
    Generate complete pipeline artifacts from user prompt + data profile.
    Enhanced with data quality context and production patterns.
    """
    logger.info("Starting pipeline generation", extra={"component": "builder"})

    # Build enhanced context with quality insights
    quality_context = ""
    if quality_report:
        critical = [c for c in quality_report.get("checks", []) if c["severity"] == "critical"]
        warnings = [c for c in quality_report.get("checks", []) if c["severity"] == "warning"]
        pii_cols = quality_report.get("pii_columns", [])

        quality_context = f"""

## Data Quality Report (AUTO-DETECTED ISSUES — address these in your ETL code):
- Quality Score: {quality_report.get('quality_score', 'N/A')}/100
- Critical Issues ({len(critical)}): {json.dumps([c['description'] for c in critical], default=str)}
- Warnings ({len(warnings)}): {json.dumps([c['description'] for c in warnings], default=str)}
- PII Columns Detected: {pii_cols if pii_cols else 'None'}

YOU MUST handle each critical issue in your generated ETL code."""

    user_message = f"""## User Request
{prompt}

## Data Profile
{json.dumps(data_profile, indent=2, default=str)}
{quality_context}

Generate a complete, production-ready data pipeline. Return ONLY a valid JSON object."""

    try:
        content = _call_llm([
            {"role": "system", "content": BUILDER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ])

        artifacts = _parse_response(content)

        metrics.record("pipeline_generated", 1, {"success": "true"})
        logger.info(
            "Pipeline generation complete",
            extra={"component": "builder", "has_etl": bool(artifacts.get("etl_code"))},
        )

        return artifacts

    except Exception as e:
        logger.error(f"Pipeline generation failed: {str(e)}", extra={"component": "builder"})
        metrics.record("pipeline_generated", 1, {"success": "false"})

        return {
            "etl_code": "",
            "sql_schema": "",
            "airflow_dag": "",
            "mermaid_diagram": "",
            "reasoning_trace": f"Error calling GLM API: {str(e)}",
        }


def _parse_response(content: str) -> dict:
    """Robustly parse LLM response to extract JSON artifacts."""
    raw_content = content or ""

    # Try to extract JSON from markdown code blocks first
    json_match = re.search(r'```(?:json)?\s*\n?(.*)\n?```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()
    else:
        content = raw_content.strip()

    # Try direct JSON parse
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Try to find JSON object boundaries
        brace_start = content.find('{')
        brace_end = content.rfind('}')
        if brace_start != -1 and brace_end != -1:
            try:
                result = json.loads(content[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                result = _salvage_builder_fields(raw_content)
        else:
            result = _salvage_builder_fields(raw_content)

    if not isinstance(result, dict):
        result = _salvage_builder_fields(raw_content)

    # Last-resort salvage if parser produced mostly empty values.
    if not any(result.get(k) for k in ("etl_code", "sql_schema", "airflow_dag", "mermaid_diagram")):
        result = _salvage_builder_fields(raw_content, existing=result)

    # Generate fallback DAG if missing or invalid (ensures pipeline is executable)
    dag_code = result.get("airflow_dag", "").strip()
    if not dag_code or not _is_valid_airflow_dag(dag_code):
        old_dag_len = len(dag_code)
        result["airflow_dag"] = _generate_fallback_airflow_dag()
        logger.warning(
            f"Generated fallback Airflow DAG (original was {old_dag_len} chars, pass validation={_is_valid_airflow_dag(dag_code)})", 
            extra={"component": "builder"}
        )

    # Normalize keys
    return {
        "etl_code": result.get("etl_code", ""),
        "sql_schema": result.get("sql_schema", ""),
        "airflow_dag": result.get("airflow_dag", ""),
        "mermaid_diagram": result.get("mermaid_diagram", ""),
        "reasoning_trace": result.get("reasoning", result.get("reasoning_trace", "")),
    }


def _salvage_builder_fields(raw_content: str, existing: dict = None) -> dict:
    """Recover fields from malformed LLM output using regex and fenced code fallback."""
    existing = existing or {}

    def extract_json_string_field(key: str) -> str:
        # Capture until next known key, allowing broken/partial JSON payloads.
        pattern = re.compile(
            rf'"{key}"\s*:\s*"(.*?)"\s*,\s*"(?:etl_code|sql_schema|airflow_dag|mermaid_diagram|reasoning|reasoning_trace)"',
            re.DOTALL,
        )
        match = pattern.search(raw_content)
        if not match:
            # Key may be the last field before a closing brace (or truncated tail).
            tail_pattern = re.compile(rf'"{key}"\s*:\s*"(.*?)(?:"\s*\}}|$)', re.DOTALL)
            match = tail_pattern.search(raw_content)
        if not match:
            return ""
        value = match.group(1)
        # Unescape common JSON escapes where possible.
        try:
            return json.loads(f'"{value}"')
        except Exception:
            return value.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').strip()

    etl_code = existing.get("etl_code", "") or extract_json_string_field("etl_code")
    sql_schema = existing.get("sql_schema", "") or extract_json_string_field("sql_schema")
    airflow_dag = existing.get("airflow_dag", "") or extract_json_string_field("airflow_dag")
    mermaid_diagram = existing.get("mermaid_diagram", "") or extract_json_string_field("mermaid_diagram")
    reasoning = existing.get("reasoning", existing.get("reasoning_trace", "")) or extract_json_string_field("reasoning")

    # Fallback: use fenced code blocks if key extraction failed.
    if not etl_code:
        py_blocks = re.findall(r"```python\s*(.*?)```", raw_content, re.DOTALL | re.IGNORECASE)
        if py_blocks:
            etl_code = py_blocks[0].strip()
    if not airflow_dag:
        py_blocks = re.findall(r"```python\s*(.*?)```", raw_content, re.DOTALL | re.IGNORECASE)
        if len(py_blocks) > 1:
            airflow_dag = py_blocks[1].strip()
    if not sql_schema:
        sql_blocks = re.findall(r"```sql\s*(.*?)```", raw_content, re.DOTALL | re.IGNORECASE)
        if sql_blocks:
            sql_schema = sql_blocks[0].strip()
    if not mermaid_diagram:
        mermaid_blocks = re.findall(r"```mermaid\s*(.*?)```", raw_content, re.DOTALL | re.IGNORECASE)
        if mermaid_blocks:
            mermaid_diagram = mermaid_blocks[0].strip()

    if not reasoning:
        reasoning = f"Failed to parse LLM response cleanly. Raw output:\n{raw_content[:2000]}"

    return {
        "etl_code": etl_code,
        "sql_schema": sql_schema,
        "airflow_dag": airflow_dag,
        "mermaid_diagram": mermaid_diagram,
        "reasoning": reasoning,
    }


def _generate_fallback_airflow_dag() -> str:
    """
    Generate a baseline Airflow DAG when LLM parsing fails.
    Ensures pipeline is always executable even with incomplete LLM response.
    """
    return '''from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

# Fallback DAG (generated due to LLM response truncation)
default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "data_pipeline_etl",
    default_args=default_args,
    description="Enterprise data pipeline with idempotency and healing",
    schedule_interval="0 8 * * *",  # Daily at 8 AM
    catchup=False,
    tags=["etl", "production"],
)


def extract_task():
    """Extract data from source (CSV)"""
    print("[EXTRACT] Reading source CSV...")
    

def transform_task():
    """Transform and validate data"""
    print("[TRANSFORM] Processing data...")


def load_task():
    """Load data to destination (SQLite)"""
    print("[LOAD] Writing to database...")


extract = PythonOperator(
    task_id="extract",
    python_callable=extract_task,
    dag=dag,
)

transform = PythonOperator(
    task_id="transform",
    python_callable=transform_task,
    dag=dag,
)

load = PythonOperator(
    task_id="load",
    python_callable=load_task,
    dag=dag,
)

extract >> transform >> load
'''


def _is_valid_airflow_dag(dag_code: str) -> bool:
    """Check if DAG code contains minimum required elements."""
    if not dag_code or len(dag_code.strip()) < 50:
        return False
    
    # Check for essential Airflow DAG elements
    has_dag_import = "from airflow import DAG" in dag_code or "import airflow" in dag_code
    has_dag_definition = "dag = DAG(" in dag_code or "DAG(" in dag_code
    has_operators = "PythonOperator" in dag_code or "BashOperator" in dag_code or "Operator" in dag_code
    has_task_dependencies = ">>" in dag_code or "set_upstream" in dag_code or "set_downstream" in dag_code
    
    # At least 3 of 4 critical elements should be present
    critical_count = sum([has_dag_import, has_dag_definition, has_operators, has_task_dependencies])
    return critical_count >= 3

