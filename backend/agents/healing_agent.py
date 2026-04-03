"""
Enterprise-Grade Healing Agent
Uses GLM 5.1 for autonomous monitoring, issue detection, and self-healing.
Incorporates: production risk analysis, security audit, performance optimization,
idempotency verification, and cost optimization recommendations.
"""

import json
import re
from zhipuai import ZhipuAI
from config import ZHIPUAI_API_KEY, GLM_MODEL
from engine.monitoring import get_logger, metrics
from engine.retry import retry_with_backoff, RetryConfig, CircuitBreaker

logger = get_logger("healing_agent")
client = ZhipuAI(
    api_key=ZHIPUAI_API_KEY,
    base_url="https://api.z.ai/api/coding/paas/v4"
)

llm_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0, name="glm_healer")

HEALING_SYSTEM_PROMPT = """You are a Senior Data Pipeline Reliability Engineer and Security Auditor.
You analyze pipeline simulation results and provide fixes for production readiness.

Think like a Site Reliability Engineer at Netflix or Uber reviewing code before production deployment.

## Your Analysis MUST Cover These Dimensions:

### 1. Execution Correctness
- Did the ETL code run without errors?
- Are row counts consistent (no silent data loss)?
- Do output tables have expected columns and types?

### 2. Data Quality
- Are nulls handled properly (not silently dropped)?
- Are duplicates removed with an idempotent strategy (MERGE/UPSERT)?
- Are type conversions safe (no silent truncation)?
- Are outliers handled or flagged?

### 3. Production Risks
- Is the code idempotent (safe to re-run)?
- Are there hardcoded values that should be configurable?
- Is error handling comprehensive (no bare except)?
- Are there race conditions or resource leaks?

### 4. Security & Compliance
- Is PII data masked/encrypted/hashed appropriately?
- Are database credentials externalized (not hardcoded)?
- Are SQL queries parameterized (no injection risk)?
- Is access control considered?

### 5. Performance & Scalability
- Are there full-table scans that should use indexes?
- Should any operations use chunked processing for large data?
- Are there unnecessary copies of large DataFrames?
- Is partitioning strategy appropriate?

### 6. DAG Quality
- Does the DAG have proper retry logic?
- Are SLAs defined?
- Are task dependencies correct?
- Is the schedule appropriate?

You MUST respond with a SINGLE valid JSON object:
{
  "has_issues": true/false,
  "issues": [
    {
      "severity": "critical|warning|info",
      "category": "execution_error|data_quality|production_risk|security|performance|dag_quality",
      "description": "Clear description",
      "fix": "Specific fix description",
      "line_reference": "Optional: which part of code to change"
    }
  ],
  "fixed_etl_code": "COMPLETE fixed ETL code (or empty string if no changes)",
  "fixed_sql_schema": "COMPLETE fixed SQL schema (or empty string if no changes)",
  "fixed_airflow_dag": "COMPLETE fixed Airflow DAG (or empty string if no changes)",
  "fixed_mermaid_diagram": "Updated diagram or empty string",
  "reasoning": "Detailed analysis explaining each issue and why your fix resolves it",
  "readiness_score": {
    "overall": 0-100,
    "data_quality": 0-100,
    "code_quality": 0-100,
    "dag_validity": 0-100,
    "error_handling": 0-100,
    "security": 0-100,
    "performance": 0-100,
    "details": ["List of specific readiness notes"]
  }
}

CRITICAL RULES:
1. Fixed code must be COMPLETE and self-contained (not patches)
2. ETL code reads from `csv_path`, writes to `db_path` (pre-defined variables)
3. Only use: pandas (pd), sqlite3, datetime in ETL code
4. Even if simulation succeeded, check for production risks
5. ALWAYS provide readiness_score
6. Return ONLY valid JSON — no markdown formatting"""


@retry_with_backoff(RetryConfig(max_retries=2, base_delay=2.0))
def _call_llm(messages: list) -> str:
    """Call GLM API with retry and circuit breaker."""
    def make_call():
        response = client.chat.completions.create(
            model=GLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=8000,
        )
        return response.choices[0].message.content.strip()

    return llm_breaker.call(make_call)


def analyze_and_heal(
    original_prompt: str,
    etl_code: str,
    sql_schema: str,
    airflow_dag: str,
    simulation_result: dict,
    dag_validation: dict,
    sql_validation: dict,
    data_profile: dict,
    iteration: int,
    user_feedback: str = "",
    quality_report: dict = None,
) -> dict:
    """
    Analyze simulation results and auto-fix issues.
    Now includes quality report context and enhanced security analysis.
    """
    logger.info(
        f"Starting healing analysis (iteration {iteration})",
        extra={"iteration": iteration, "component": "healer"},
    )

    feedback_section = ""
    if user_feedback:
        feedback_section = f"\n\n## User Feedback (MUST ADDRESS)\n{user_feedback}"

    quality_section = ""
    if quality_report:
        quality_section = f"\n\n## Auto-Detected Data Quality Issues\n{json.dumps(quality_report, indent=2, default=str)}"

    user_message = f"""## Original Request
{original_prompt}

## Current ETL Code
```python
{etl_code}
```

## Current SQL Schema
```sql
{sql_schema}
```

## Current Airflow DAG
```python
{airflow_dag}
```

## Simulation Results (Iteration {iteration})
{json.dumps(simulation_result, indent=2, default=str)}

## DAG Validation
{json.dumps(dag_validation, indent=2, default=str)}

## SQL Validation
{json.dumps(sql_validation, indent=2, default=str)}

## Data Profile
{json.dumps(data_profile, indent=2, default=str)}
{quality_section}
{feedback_section}

Perform a comprehensive production readiness analysis. Return ONLY a valid JSON object."""

    try:
        content = _call_llm([
            {"role": "system", "content": HEALING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ])

        result = _parse_response(content)

        issue_count = len(result.get("issues", []))
        metrics.record("healing_issues_found", issue_count, {"iteration": str(iteration)})
        logger.info(
            f"Healing analysis complete: {issue_count} issues found",
            extra={"iteration": iteration, "component": "healer"},
        )

        return _normalize_result(result)

    except Exception as e:
        logger.error(f"Healing analysis failed: {str(e)}", extra={"component": "healer"})
        return _fallback_result(f"GLM API error: {str(e)}")


def _parse_response(content: str) -> dict:
    """Robustly parse healing response."""
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        brace_start = content.find('{')
        brace_end = content.rfind('}')
        if brace_start != -1 and brace_end != -1:
            try:
                return json.loads(content[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass
        return None


def _normalize_result(result: dict) -> dict:
    """Normalize the healing result to expected format."""
    if result is None:
        return _fallback_result("Could not parse healing response")

    readiness = result.get("readiness_score", {})
    if isinstance(readiness, (int, float)):
        readiness = {"overall": int(readiness), "details": []}

    return {
        "has_issues": result.get("has_issues", False),
        "issues": result.get("issues", []),
        "fixed_etl_code": result.get("fixed_etl_code", ""),
        "fixed_sql_schema": result.get("fixed_sql_schema", ""),
        "fixed_airflow_dag": result.get("fixed_airflow_dag", ""),
        "fixed_mermaid_diagram": result.get("fixed_mermaid_diagram", ""),
        "reasoning": result.get("reasoning", ""),
        "readiness_score": {
            "overall": readiness.get("overall", 50),
            "data_quality": readiness.get("data_quality", 50),
            "code_quality": readiness.get("code_quality", 50),
            "dag_validity": readiness.get("dag_validity", 50),
            "error_handling": readiness.get("error_handling", 50),
            "security": readiness.get("security", 50),
            "performance": readiness.get("performance", 50),
            "details": readiness.get("details", []),
        },
    }


def _fallback_result(error_msg: str) -> dict:
    """Safe fallback when parsing fails."""
    return {
        "has_issues": False,
        "issues": [],
        "fixed_etl_code": "",
        "fixed_sql_schema": "",
        "fixed_airflow_dag": "",
        "fixed_mermaid_diagram": "",
        "reasoning": f"Could not parse healing response: {error_msg[:1000]}",
        "readiness_score": {
            "overall": 50,
            "data_quality": 50,
            "code_quality": 50,
            "dag_validity": 50,
            "error_handling": 50,
            "security": 50,
            "performance": 50,
            "details": ["Healing analysis incomplete — manual review recommended"],
        },
    }
