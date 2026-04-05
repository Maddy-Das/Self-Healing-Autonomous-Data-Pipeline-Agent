import requests
import time

# Quick test of the healing parsing fix
print('Testing healing agent parsing improvements...')

# Create a simple test
files = {'file': open('sample_data/sales_data.csv', 'rb')}
data = {'prompt': 'Create a simple sales pipeline'}
try:
    response = requests.post('http://127.0.0.1:8000/api/pipeline/create', files=files, data=data, timeout=30)
    if response.status_code == 200:
        session_id = response.json()['session_id']
        print(f'Created session: {session_id}')

        # Wait a bit and check status
        time.sleep(5)
        status_response = requests.get(f'http://127.0.0.1:8000/api/pipeline/{session_id}/status', timeout=10)
        status = status_response.json()
        print(f'Current status: {status["status"]}')
        if 'healer_reasoning' in status and status['healer_reasoning']:
            print(f'Healing reasoning length: {len(status["healer_reasoning"])}')
            print(f'Has issues detected: {"issues" in status and len(status.get("issues", [])) > 0}')
    else:
        print(f'Failed to create pipeline: {response.status_code}')
except Exception as e:
    print(f'Error: {e}')