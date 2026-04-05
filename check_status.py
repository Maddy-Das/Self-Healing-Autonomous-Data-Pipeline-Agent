import requests

status_response = requests.get('http://127.0.0.1:8000/api/pipeline/56f3a9cd/status', timeout=10)
status = status_response.json()
print(f'Status: {status["status"]}')
if 'healer_reasoning' in status and status['healer_reasoning']:
    print(f'Healing reasoning preview: {status["healer_reasoning"][:200]}...')
if 'simulation_result' in status and status['simulation_result']:
    sim = status['simulation_result']
    print(f'Simulation: success={sim.get("success")}, errors={len(sim.get("errors", []))}')
else:
    print('No simulation result yet')