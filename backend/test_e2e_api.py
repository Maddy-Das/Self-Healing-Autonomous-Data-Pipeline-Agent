import requests
import time

try:
    # Upload sample CSV and trigger pipeline
    with open('sample_data/sales_data.csv', 'rb') as f:
        resp = requests.post(
            'http://localhost:8000/api/pipeline/create',
            files={'file': ('sales_data.csv', f, 'text/csv')},
            data={'prompt': 'Ingest sales data, clean nulls and duplicates, calculate total revenue per region, flag anomalies'}
        )

    resp.raise_for_status()
    data = resp.json()
    session_id = data['session_id']
    print(f'Session created: {session_id}')
    print(f'Initial status: {data["status"]}')

    # Poll for completion (max 180s for LLM calls)
    for i in range(90):
        time.sleep(2)
        status_resp = requests.get(f'http://localhost:8000/api/pipeline/{session_id}/status')
        status_resp.raise_for_status()
        status_data = status_resp.json()
        current = status_data['status']
        print(f'  [{i*2}s] Status: {current}')
        
        if current in ('complete', 'error'):
            print(f'\nFinal status: {current}')
            
            if current == 'error':
                print(f'Error: {status_data.get("error_message", "unknown")}')
            
            # Show quality report
            qr = status_data.get('quality_report', {})
            if qr:
                print(f'Quality Score: {qr.get("quality_score")}/100')
                print(f'Critical Issues: {qr.get("critical_count")}')
                print(f'PII Detected: {qr.get("pii_detected")}')
                print(f'PII Columns: {qr.get("pii_columns")}')
            
            # Show readiness
            readiness = status_data.get('readiness', {})
            if readiness:
                print(f'Readiness Score: {readiness.get("overall")}/100')
            
            # Show artifacts
            arts = status_data.get('artifacts', {})
            print(f'ETL Code: {len(arts.get("etl_code", ""))} chars')
            print(f'SQL Schema: {len(arts.get("sql_schema", ""))} chars')
            print(f'DAG: {len(arts.get("airflow_dag", ""))} chars')
            print(f'Mermaid: {len(arts.get("mermaid_diagram", ""))} chars')
            
            # Show healing history
            history = status_data.get('healing_history', [])
            print(f'Healing Iterations: {len(history)}')
            for h in history:
                print(f'  Iteration {h["iteration"]}: {len(h.get("issues_found", []))} issues')
            
            break
    else:
        print('Timed out waiting for pipeline completion')

except Exception as e:
    print(f'Test failed: {str(e)}')
