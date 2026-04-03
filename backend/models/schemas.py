from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PipelineStatus(str, Enum):
    UPLOADING = "uploading"
    PROFILING = "profiling"
    GENERATING = "generating"
    SIMULATING = "simulating"
    HEALING = "healing"
    COMPLETE = "complete"
    ERROR = "error"


class PipelineCreateRequest(BaseModel):
    prompt: str


class HealRequest(BaseModel):
    feedback: Optional[str] = None


class DataProfile(BaseModel):
    row_count: int
    column_count: int
    columns: list[dict]
    sample_rows: list[dict]
    file_name: str


class SimulationResult(BaseModel):
    success: bool
    logs: list[str]
    errors: list[str]
    input_rows: int
    output_rows: int
    execution_time_ms: float
    sample_output: list[dict]
    dag_validation: Optional[dict] = None
    sql_validation: Optional[dict] = None


class HealingIteration(BaseModel):
    iteration: int
    issues_found: list[str]
    fixes_applied: list[str]
    reasoning: str
    simulation_after: Optional[SimulationResult] = None


class PipelineArtifacts(BaseModel):
    etl_code: str = ""
    sql_schema: str = ""
    airflow_dag: str = ""
    mermaid_diagram: str = ""
    reasoning_trace: str = ""
    docker_compose: str = ""
    readme: str = ""


class ReadinessReport(BaseModel):
    overall_score: int = 0
    data_quality_score: int = 0
    code_quality_score: int = 0
    dag_validity_score: int = 0
    error_handling_score: int = 0
    details: list[str] = []


class PipelineSession(BaseModel):
    session_id: str
    status: PipelineStatus = PipelineStatus.UPLOADING
    prompt: str = ""
    data_profile: Optional[DataProfile] = None
    artifacts: PipelineArtifacts = PipelineArtifacts()
    simulation_result: Optional[SimulationResult] = None
    healing_history: list[HealingIteration] = []
    readiness: ReadinessReport = ReadinessReport()
    builder_reasoning: str = ""
    healer_reasoning: str = ""
    error_message: str = ""
    csv_path: str = ""
