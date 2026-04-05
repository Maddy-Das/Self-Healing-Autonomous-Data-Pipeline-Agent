#!/usr/bin/env python
"""
Quick validation test for pipeline generation fixes
Shows: DAG generation, artifact sizes, readiness score
"""
import requests
import time
import json

print("=" * 70)
print("SELF-HEALING PIPELINE - VALIDATION TEST")
print("=" * 70)

# Create pipeline
print("\n[1/3] Creating pipeline session...")
with open('sample_data/sales_data.csv', 'rb') as f:
    r = requests.post(
        'http://127.0.0.1:8000/api/pipeline/create', 
        files={'file': f},
        data={'prompt': 'Sales data ETL pipeline with quality checks and error handling'}
    )

if r.status_code != 200:
    print(f"ERROR: Failed to create pipeline: {r.text}")
    exit(1)

session_id = r.json()['session_id']
print(f"✓ Session created: {session_id}")

# Poll for completion
print("\n[2/3] Waiting for pipeline generation (this takes 4-5 minutes)...")
start_time = time.time()
max_wait = 400  # 6+ minutes max
poll_interval = 10

completed = False
for i in range(max_wait // poll_interval):
    r = requests.get(f'http://127.0.0.1:8000/api/pipeline/{session_id}/status')
    s = r.json()
    
    if s['status'] in ['complete', 'error']:
        completed = True
        elapsed = time.time() - start_time
        print(f"\n✓ Pipeline {s['status']}: {elapsed:.0f}s")
        break
    
    if i % 3 == 0:  # Print every 30 seconds
        print(f"  [{int((time.time() - start_time)/60):02d}:{int((time.time() - start_time)%60):02d}s] Status: {s['status']}")
    
    time.sleep(poll_interval)

if not completed:
    print("✗ Pipeline processing timed out")
    exit(1)

# Check artifacts
print("\n[3/3] Validating generated artifacts...")
artifacts = s.get('artifacts', {})
etl_code = artifacts.get('etl_code', '')
sql_schema = artifacts.get('sql_schema', '')
airflow_dag = artifacts.get('airflow_dag', '')
mermaid_diagram = artifacts.get('mermaid_diagram', '')

# Validate artifacts
print(f"\n  ETL Code:     {len(etl_code):6d} chars ({'✓' if len(etl_code) > 500 else '✗'})")
print(f"  SQL Schema:   {len(sql_schema):6d} chars ({'✓' if len(sql_schema) > 200 else '✗'})")
print(f"  Airflow DAG:  {len(airflow_dag):6d} chars ({'✓' if len(airflow_dag) > 300 else '✗'})")
print(f"  Mermaid Diag: {len(mermaid_diagram):6d} chars ({'✓' if len(mermaid_diagram) > 100 else '✗'})")

# Check DAG validity
has_dag_import = "from airflow import DAG" in airflow_dag
has_dag_def = "dag = DAG(" in airflow_dag or "DAG(" in airflow_dag
has_ops = "Operator" in airflow_dag  
has_deps = ">>" in airflow_dag or "set_upstream" in airflow_dag

dag_valid = sum([has_dag_import, has_dag_def, has_ops, has_deps]) >= 3
print(f"\n  DAG Validity: {'✓ VALID' if dag_valid else '✗ INVALID'}")
if not dag_valid:
    print(f"    Import: {has_dag_import}, Definition: {has_dag_def}, Operators: {has_ops}, Dependencies: {has_deps}")

# Check for healing
healing_history = s.get('healing_history', [])
print(f"\n  Healing iterations: {len(healing_history)}")
for i, h in enumerate(healing_history, 1):
    issues = len(h.get('issues_found', []))
    print(f"    Iteration {i}: {issues} issues found")

# Readiness score
readiness = s.get('readiness', {})
overall_score = readiness.get('overall', 0)
print(f"\n  Readiness Score: {overall_score}/100")
if overall_score <= 50:
    print(f"    ⚠️  Score is {overall_score}/100 - pipeline may need manual review")
else:
    print(f"    ✓ Score is {overall_score}/100 - pipeline ready for testing")

# Show DAG sample
if airflow_dag and dag_valid:
    print(f"\n  DAG Sample (first 300 chars):")
    print("  " + "-" * 66)
    for line in airflow_dag[:300].split('\n'):
        print(f"  {line}")
    if len(airflow_dag) > 300:
        print(f"  ... ({len(airflow_dag) - 300} more chars)")
    print("  " + "-" * 66)

print("\n" + "=" * 70)
if dag_valid and len(etl_code) > 500 and readiness.get('overall', 0) >= 50:
    print("✓ VALIDATION PASSED - All artifacts generated successfully")
else:
    print("✗ VALIDATION ISSUES - Review artifacts above")
print("=" * 70)

# Save session ID for debugging
with open('last_session.txt', 'w') as f:
    f.write(session_id)
print(f"\nSession ID saved to: last_session.txt")
