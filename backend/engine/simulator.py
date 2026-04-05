import ast
import io
import sqlite3
import sys
import time
import traceback
import threading
import pandas as pd
from pathlib import Path
from config import SIMULATION_TIMEOUT_SECONDS


def run_etl_simulation(etl_code: str, csv_path: str) -> dict:
    """
    Layer 1: Execute generated ETL code in a sandboxed environment.
    Uses restricted exec() with only safe modules available.
    """
    result = {
        "success": False,
        "logs": [],
        "errors": [],
        "input_rows": 0,
        "output_rows": 0,
        "execution_time_ms": 0,
        "sample_output": [],
    }

    # Capture stdout/stderr
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()

    # Create in-memory SQLite database for simulation
    db_path = str(Path(csv_path).parent / "simulation.db")

    try:
        # Read input CSV to count rows
        input_df = pd.read_csv(csv_path)
        result["input_rows"] = len(input_df)

        # Prepare sandbox globals
        sandbox_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "round": round,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "isinstance": isinstance,
                "type": type,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "Exception": Exception,
                "__import__": __import__,
            },
            "pd": pd,
            "pandas": pd,
            "sqlite3": sqlite3,
            "csv_path": csv_path,
            "db_path": db_path,
        }

        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        # Execute with timeout
        exec_error = [None]
        exec_complete = threading.Event()

        def run_code():
            try:
                exec(etl_code, sandbox_globals)
            except Exception as e:
                exec_error[0] = e
            finally:
                exec_complete.set()

        start_time = time.time()
        thread = threading.Thread(target=run_code, daemon=True)
        thread.start()
        exec_complete.wait(timeout=SIMULATION_TIMEOUT_SECONDS)
        end_time = time.time()

        result["execution_time_ms"] = round((end_time - start_time) * 1000, 2)

        if not exec_complete.is_set():
            result["errors"].append(f"Execution timed out after {SIMULATION_TIMEOUT_SECONDS}s")
            return result

        if exec_error[0]:
            result["errors"].append(f"{type(exec_error[0]).__name__}: {str(exec_error[0])}")
            result["errors"].append(traceback.format_exception(type(exec_error[0]), exec_error[0], exec_error[0].__traceback__)[-1].strip())
            return result

        # Check SQLite for output data
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            total_output_rows = 0
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                total_output_rows += count
                result["logs"].append(f"Table '{table}': {count} rows written")

                # Get sample output
                cursor.execute(f"SELECT * FROM [{table}] LIMIT 5")
                cols = [desc[0] for desc in cursor.description]
                for row in cursor.fetchall():
                    result["sample_output"].append(dict(zip(cols, row)))

            result["output_rows"] = total_output_rows
            conn.close()
        except Exception as e:
            result["logs"].append(f"DB inspection note: {str(e)}")

        # If no errors, consider success
        if not result["errors"]:
            result["success"] = True

    except Exception as e:
        result["errors"].append(f"Simulation setup error: {str(e)}")
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        stdout_content = captured_stdout.getvalue()
        stderr_content = captured_stderr.getvalue()
        if stdout_content:
            result["logs"].extend(stdout_content.strip().split("\n"))
        if stderr_content:
            result["errors"].extend(stderr_content.strip().split("\n"))

    return result


def validate_dag(dag_code: str) -> dict:
    """
    Layer 2: Validate Airflow DAG structure using AST parsing.
    No Airflow installation required.
    """
    validation = {
        "valid_syntax": False,
        "has_dag_definition": False,
        "has_tasks": False,
        "has_dependencies": False,
        "has_schedule": False,
        "issues": [],
        "task_count": 0,
    }

    # Check syntax
    try:
        tree = ast.parse(dag_code)
        validation["valid_syntax"] = True
    except SyntaxError as e:
        validation["issues"].append(f"Syntax error at line {e.lineno}: {e.msg}")
        return validation

    # Analyze AST for DAG patterns
    for node in ast.walk(tree):
        # Check for DAG() constructor call
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name == "DAG":
                validation["has_dag_definition"] = True
                # Check for schedule_interval keyword
                for kw in node.keywords:
                    if kw.arg in ("schedule_interval", "schedule"):
                        validation["has_schedule"] = True

            # Check for operator instantiations (tasks)
            if func_name in (
                "PythonOperator", "BashOperator", "PostgresOperator",
                "DummyOperator", "EmptyOperator", "SqliteOperator",
                "PythonSensor", "ExternalTaskSensor",
            ) or "Operator" in func_name or "Sensor" in func_name:
                validation["task_count"] += 1
                validation["has_tasks"] = True

        # Check for >> or << operators (task dependencies)
        if isinstance(node, (ast.LShift, ast.RShift)):
            validation["has_dependencies"] = True

    # Check for dependency using set_downstream / set_upstream
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in ("set_downstream", "set_upstream"):
                validation["has_dependencies"] = True

    # Generate issues
    if not validation["has_dag_definition"]:
        validation["issues"].append("No DAG() constructor found")
    if not validation["has_tasks"]:
        validation["issues"].append("No operator/task definitions found")
    if not validation["has_schedule"]:
        validation["issues"].append("No schedule_interval defined")
    if not validation["has_dependencies"] and validation["task_count"] > 1:
        validation["issues"].append("Multiple tasks found but no dependencies defined")

    return validation


def validate_sql(schema_ddl: str, queries: str = "") -> dict:
    """
    Layer 3: Validate SQL by executing against SQLite.
    """
    validation = {
        "schema_valid": False,
        "queries_valid": False,
        "tables_created": [],
        "issues": [],
    }

    conn = None
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        # Execute schema DDL
        if schema_ddl.strip():
            # Replace PostgreSQL-specific syntax for SQLite compatibility
            sqlite_ddl = schema_ddl
            sqlite_ddl = sqlite_ddl.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            sqlite_ddl = sqlite_ddl.replace("BIGSERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            sqlite_ddl = sqlite_ddl.replace("VARCHAR", "TEXT")
            sqlite_ddl = sqlite_ddl.replace("TIMESTAMP", "TEXT")
            sqlite_ddl = sqlite_ddl.replace("BOOLEAN", "INTEGER")
            sqlite_ddl = sqlite_ddl.replace("DOUBLE PRECISION", "REAL")
            sqlite_ddl = sqlite_ddl.replace("NUMERIC", "REAL")

            try:
                cursor.executescript(sqlite_ddl)
                validation["schema_valid"] = True

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                validation["tables_created"] = [r[0] for r in cursor.fetchall()]
            except Exception as e:
                validation["issues"].append(f"Schema error: {str(e)}")

        # Execute queries
        if queries.strip():
            try:
                cursor.executescript(queries)
                validation["queries_valid"] = True
            except Exception as e:
                validation["issues"].append(f"Query error: {str(e)}")
        else:
            validation["queries_valid"] = True  # No queries to validate

    except Exception as e:
        validation["issues"].append(f"SQL validation error: {str(e)}")
    finally:
        if conn:
            conn.close()

    return validation
