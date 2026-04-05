import time
import requests

start_time = time.time()

files = {'file': open('sample_data/sales_data.csv', 'rb')}
data = {'prompt': 'Create a sales analytics pipeline'}
response = requests.post('http://127.0.0.1:8000/api/pipeline/create', files=files, data=data)
session_id = response.json()['session_id']

print(f'Session created: {session_id}')

while True:
    status_response = requests.get(f'http://127.0.0.1:8000/api/pipeline/{session_id}/status')
    status = status_response.json()

    current_time = time.time() - start_time
    print(f'[{current_time:.1f}s] {status["status"]}')

    if status['status'] in ['complete', 'error']:
        break

    time.sleep(5)

total_time = time.time() - start_time
print(f'Total time: {total_time:.1f}s')