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
4. Print progress messages using print()
5. Implement these PRODUCTION patterns:
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

Return ONLY the JSON object — no markdown, no explanation outside the JSON."""


@retry_with_backoff(RetryConfig(max_retries=2, base_delay=2.0))
def _call_llm(messages: list) -> str:
    """Call GLM API with retry and circuit breaker protection."""
    def make_call():
        response = client.chat.completions.create(
            model=GLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=8000,
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
    # Try to extract JSON from markdown code blocks first
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()

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
                result = {
                    "etl_code": "",
                    "sql_schema": "",
                    "airflow_dag": "",
                    "mermaid_diagram": "",
                    "reasoning": f"Failed to parse LLM response. Raw output:\n{content[:2000]}",
                }
        else:
            result = {
                "etl_code": "",
                "sql_schema": "",
                "airflow_dag": "",
                "mermaid_diagram": "",
                "reasoning": f"No JSON found in LLM response. Raw output:\n{content[:2000]}",
            }

    # Normalize keys
    return {
        "etl_code": result.get("etl_code", ""),
        "sql_schema": result.get("sql_schema", ""),
        "airflow_dag": result.get("airflow_dag", ""),
        "mermaid_diagram": result.get("mermaid_diagram", ""),
        "reasoning_trace": result.get("reasoning", result.get("reasoning_trace", "")),
    }
