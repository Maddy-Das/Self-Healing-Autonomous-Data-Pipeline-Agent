import requests, time

with open('sample_data/sales_data.csv', 'rb') as f:
    sid = requests.post('http://127.0.0.1:8000/api/pipeline/create', 
        files={'file': f}, data={'prompt': 'ETL pipeline'}).json()['session_id']

print(f'Session: {sid}')

start = time.time()
last_status = None

for i in range(600):
    r = requests.get(f'http://127.0.0.1:8000/api/pipeline/{sid}/status')
    s = r.json()
    status = s['status']
    
    if status != last_status:
        elapsed = time.time() - start
        print(f'[{elapsed:.0f}s] {status}')
        last_status = status
    
    if status in ['complete', 'error']:
        elapsed = time.time() - start
        print(f'\nDone: {status} at {elapsed:.0f}s')
        healing = s.get('healing_history', [])
        print(f'Healing iterations: {len(healing)}')
        readiness = s.get('readiness', {}).get('overall', 0)
        print(f'Readiness: {readiness}/100')
        break
    
    time.sleep(2)
