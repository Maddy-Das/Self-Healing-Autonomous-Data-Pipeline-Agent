#!/usr/bin/env python
"""Quick test to check artifact generation"""
import requests
import time

# Upload and create pipeline
with open('sample_data/sales_data.csv', 'rb') as f:
    r = requests.post('http://127.0.0.1:8000/api/pipeline/create', 
        files={'file': f},
        data={'prompt': 'Create a simple ETL pipeline'})
    
session_id = r.json()['session_id']
print(f'Session: {session_id}')

# Wait for completion
for i in range(300):
    r = requests.get(f'http://127.0.0.1:8000/api/pipeline/{session_id}/status')
    s = r.json()
    if s['status'] in ['complete', 'error']:
        print(f"Status: {s['status']}")
        artifacts = s.get('artifacts', {})
        etl_len = len(artifacts.get('etl_code', ''))
        sql_len = len(artifacts.get('sql_schema', ''))
        dag_len = len(artifacts.get('airflow_dag', ''))
        print(f"Artifacts: etl={etl_len} sql={sql_len} dag={dag_len}")
        
        if artifacts.get('airflow_dag'):
            print("DAG first 300 chars:")
            print(artifacts['airflow_dag'][:300])
        else:
            print("DAG is empty!")
            
        # Check error
        if s.get('error_message'):
            print(f"Error: {s['error_message']}")
        break
    time.sleep(1)
    if i % 10 == 0:
        print(f"[{i}s] Status: {s['status']}")

print("Done!")
