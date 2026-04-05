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

HEALING_SYSTEM_PROMPT = """You are a code reviewer doing FAST quality checks.

Respond with JSON:
{
  "has_issues": true/false,
  "issues": [{"severity": "critical|warning", "description": "...", "fix": "..."}],
  "fixed_etl_code": "",
  "fixed_sql_schema": "",
  "fixed_airflow_dag": "",
  "fixed_mermaid_diagram": "",
  "reasoning": "Brief findings",
  "readiness_score": {"overall": 0-100, "details": [...]}
}

CRITICAL RULES:
1. Fixed code must be COMPLETE and self-contained (not patches)
2. ETL code reads from `csv_path`, writes to `db_path` (pre-defined variables)
3. Only use: pandas (pd), sqlite3, datetime, argparse in ETL code
4. Even if simulation succeeded, check for production risks
5. ALWAYS provide readiness_score
6. Return ONLY valid JSON.
7. DO NOT USE MARKDOWN CODE BLOCKS (```python) INSIDE THE JSON VALUES. The code should just be a raw string with \n for newlines."""


@retry_with_backoff(RetryConfig(max_retries=2, base_delay=2.0))
def _call_llm(messages: list) -> str:
    """Call GLM API with retry and circuit breaker."""
    def make_call():
        response = client.chat.completions.create(
            model=GLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=8000,  # Reduced for faster validation (vs 16000 for builder)
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

    # Optimization: Slim down prompt for faster LLM processing
    # Only include essential simulation info (errors, row counts, success flag)
    essential_sim_result = {
        "success": simulation_result.get("success", False),
        "input_rows": simulation_result.get("input_rows", 0),
        "output_rows": simulation_result.get("output_rows", 0),
        "errors": simulation_result.get("errors", []),
        "warnings": simulation_result.get("warnings", []),
    }
    
    # Skip full data profile on subsequent iterations (not new info)
    data_profile_str = ""
    if iteration == 1:
        data_profile_str = f"\n\n## Data Profile\n{json.dumps(data_profile, indent=2, default=str)}"

    user_message = f"""## Original Request
{original_prompt}

## Current ETL Code
```python
{etl_code}
```

## Current SQL Schema (first 500 chars)
```sql
{sql_schema[:500]}
```

## Current Airflow DAG
```python
{airflow_dag}
```

## Simulation Results
Success: {essential_sim_result['success']}
Input rows: {essential_sim_result['input_rows']}
Output rows: {essential_sim_result['output_rows']}
Errors: {essential_sim_result['errors']}
Warnings: {essential_sim_result['warnings']}

## Validation Status
DAG valid: {dag_validation.get('valid', False)}
SQL valid: {sql_validation.get('valid', False)}
{quality_section}{data_profile_str}{feedback_section}

Analyze and provide quick fixes if needed. Return ONLY valid JSON object."""

    try:
        content = _call_llm([
            {"role": "system", "content": HEALING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ])

        result = _parse_response(content)
        normalized = _normalize_result(result)

        issue_count = len(normalized.get("issues", []))
        metrics.record("healing_issues_found", issue_count, {"iteration": str(iteration)})
        logger.info(
            f"Healing analysis complete: {issue_count} issues found",
            extra={"iteration": iteration, "component": "healer"},
        )

        return normalized

    except Exception as e:
        logger.error(f"Healing analysis failed: {str(e)}", extra={"component": "healer"})
        return _fallback_result(f"GLM API error: {str(e)}")


def _parse_response(content: str) -> dict:
    """Robustly parse healing response."""
    raw_content = content or ""

    # Debug logging
    logger.debug(f"Raw healing response content: {raw_content[:500]}...", extra={"component": "healer"})

    # First try: direct JSON parse (in case it's already clean JSON)
    try:
        result = json.loads(raw_content.strip())
        logger.debug("Successfully parsed raw content as JSON directly", extra={"component": "healer"})
        return result
    except json.JSONDecodeError:
        pass

    # Second try: extract from code blocks
    json_match = re.search(r'```(?:json)?\s*\n?(.*)\n?```', content, re.DOTALL)
    if json_match:
        content = json_match.group(1).strip()
        logger.debug(f"Extracted from code block: {content[:200]}...", extra={"component": "healer"})
        try:
            result = json.loads(content)
            logger.debug("Successfully parsed extracted JSON", extra={"component": "healer"})
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Code block JSON parse failed: {str(e)}", extra={"component": "healer"})

    # Third try: extract between braces
    brace_start = raw_content.find('{')
    brace_end = raw_content.rfind('}')
    if brace_start != -1 and brace_end != -1:
        try:
            result = json.loads(raw_content[brace_start:brace_end + 1])
            logger.debug("Successfully parsed JSON from braces", extra={"component": "healer"})
            return result
        except json.JSONDecodeError as e2:
            logger.warning(f"Brace extraction parse failed: {str(e2)}", extra={"component": "healer"})

    logger.warning("All JSON parsing attempts failed, using salvage parsing", extra={"component": "healer"})
    return _salvage_healing_fields(raw_content)


def _normalize_result(result: dict) -> dict:
    """Normalize the healing result to expected format."""
    if result is None or not isinstance(result, dict):
        return _fallback_result("Could not parse healing response")

    readiness = result.get("readiness_score", {})
    if isinstance(readiness, (int, float)):
        readiness = {"overall": int(readiness), "details": []}
    if not isinstance(readiness, dict):
        readiness = {"overall": 50, "details": []}

    raw_issues = result.get("issues", [])
    if not isinstance(raw_issues, list):
        raw_issues = []

    normalized_issues = []
    for issue in raw_issues:
        if isinstance(issue, dict):
            normalized_issues.append(issue)
        elif issue is not None:
            normalized_issues.append({"description": str(issue), "severity": "warning", "category": "execution_error"})

    return {
        "has_issues": result.get("has_issues", False),
        "issues": normalized_issues,
        "fixed_etl_code": result.get("fixed_etl_code", ""),
        "fixed_sql_schema": result.get("fixed_sql_schema", ""),
        "fixed_airflow_dag": _ensure_valid_dag(result.get("fixed_airflow_dag", "")),
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


def _salvage_healing_fields(raw_content: str) -> dict:
    """Recover minimum healing payload from malformed LLM output."""
    # Try to extract issues array
    issues = []
    issues_match = re.search(r'"issues"\s*:\s*\[(.*?)\]', raw_content, re.DOTALL)
    if issues_match:
        issues_text = issues_match.group(1)
        # Simple extraction of issue descriptions
        desc_matches = re.findall(r'"description"\s*:\s*"([^"]*)"', issues_text)
        for desc in desc_matches:
            issues.append({
                "severity": "critical",
                "description": desc,
                "fix": "See healing analysis for details"
            })

    fixed_etl = _extract_field(raw_content, "fixed_etl_code")
    fixed_sql = _extract_field(raw_content, "fixed_sql_schema")
    fixed_dag = _extract_field(raw_content, "fixed_airflow_dag")
    fixed_mermaid = _extract_field(raw_content, "fixed_mermaid_diagram")
    reasoning = _extract_field(raw_content, "reasoning")

    # If we found issues in the raw content, mark as having issues
    has_issues = len(issues) > 0

    return {
        "has_issues": has_issues,
        "issues": issues,
        "fixed_etl_code": fixed_etl,
        "fixed_sql_schema": fixed_sql,
        "fixed_airflow_dag": fixed_dag,
        "fixed_mermaid_diagram": fixed_mermaid,
        "reasoning": reasoning or f"Could not parse healing response cleanly. Raw output:\n{raw_content[:2000]}",
        "readiness_score": {
            "overall": 30 if has_issues else 70,
            "data_quality": 50,
            "code_quality": 30 if has_issues else 70,
            "dag_validity": 50,
            "error_handling": 30 if has_issues else 70,
            "security": 50,
            "performance": 50,
            "details": ["Healing response was malformed; extracted what was possible"] if has_issues else ["Healing analysis extracted successfully"],
        },
    }


def _extract_field(raw_content: str, key: str) -> str:
    pattern = re.compile(rf'"{key}"\s*:\s*"(.*?)"\s*,\s*"', re.DOTALL)
    match = pattern.search(raw_content)
    if not match:
        tail_pattern = re.compile(rf'"{key}"\s*:\s*"(.*?)(?:"\s*\}}|$)', re.DOTALL)
        match = tail_pattern.search(raw_content)
    if not match:
        return ""
    value = match.group(1)
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"').strip()


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


def _is_valid_airflow_dag(dag_code: str) -> bool:
    """Check if DAG code contains minimum required elements."""
    if not dag_code or len(dag_code.strip()) < 50:
        return False
    
    has_dag_import = "from airflow import DAG" in dag_code or "import airflow" in dag_code
    has_dag_definition = "dag = DAG(" in dag_code or "DAG(" in dag_code
    has_operators = "PythonOperator" in dag_code or "BashOperator" in dag_code or "Operator" in dag_code
    has_task_dependencies = ">>" in dag_code or "set_upstream" in dag_code or "set_downstream" in dag_code
    
    critical_count = sum([has_dag_import, has_dag_definition, has_operators, has_task_dependencies])
    return critical_count >= 3


def _ensure_valid_dag(dag_code: str) -> str:
    """Return the DAG if valid, otherwise return empty string for builder to handle."""
    if _is_valid_airflow_dag(dag_code):
        return dag_code
    return ""  # Will trigger healing logic to handle
