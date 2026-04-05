import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.builder_agent import _parse_response as parse_builder_response
from agents.healing_agent import _normalize_result as normalize_healing_result


def test_builder_parser_recovers_from_malformed_json_string_payload():
    malformed = '''```json
{
  "etl_code": "print(\"hello\")\nfor i in range(3):\n    print(i)",
  "sql_schema": "CREATE TABLE t(id INT);",
  "airflow_dag": "from airflow import DAG",
  "mermaid_diagram": "graph LR;A-->B",
  "reasoning": "ok"
'''

    result = parse_builder_response(malformed)

    assert result["etl_code"], "ETL code should be recovered"
    assert result["sql_schema"], "SQL schema should be recovered"
    assert result["reasoning_trace"], "Reasoning should be preserved"


def test_healing_normalize_handles_none_without_crashing():
    result = normalize_healing_result(None)

    assert isinstance(result, dict)
    assert "issues" in result
    assert isinstance(result["issues"], list)
    assert "readiness_score" in result
    assert isinstance(result["readiness_score"], dict)
