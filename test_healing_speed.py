#!/usr/bin/env python
"""Test healing optimization - should be much faster now"""
import requests
import time

print("=" * 60)
print("HEALING PHASE OPTIMIZATION TEST")
print("=" * 60)

# Create pipeline
with open('sample_data/sales_data.csv', 'rb') as f:
    r = requests.post(
        'http://127.0.0.1:8000/api/pipeline/create', 
        files={'file': f},
        data={'prompt': 'Sales ETL'}
    )

if r.status_code != 200:
    print(f"Error: {r.text}")
    exit(1)

sid = r.json()['session_id']
print(f"\nCreated session: {sid}")

# Track timing
start = time.time()
phase_times = {}
last_phase = None
last_phase_time = None

# Poll for completion
for i in range(600):  # Max 10 minutes
    r = requests.get(f'http://127.0.0.1:8000/api/pipeline/{sid}/status')
    s = r.json()
    
    status = s['status']
    
    # Track phase transitions
    if status != last_phase:
        if last_phase:
            phase_times[last_phase] = time.time() - last_phase_time
        last_phase = status
        last_phase_time = time.time()
        elapsed = time.time() - start
        print(f"[{elapsed:6.0f}s] Phase: {status:12s}")
    
    if status in ['complete', 'error']:
        elapsed = time.time() - start
        phase_times[status] = time.time() - last_phase_time
        print(f"\n✓ Done: {status} at {elapsed:.0f}s\n")
        
        # Show breakdown
        print("PHASE TIMING BREAKDOWN:")
        print("-" * 40)
        for phase, duration in phase_times.items():
            print(f"  {phase:15s}: {duration:6.1f}s")
        print("-" * 40)
        print(f"  {'TOTAL':15s}: {sum(phase_times.values()):6.1f}s")
        
        # Check artifacts
        artifacts = s.get('artifacts', {})
        print(f"\nARTIFACTS:")
        print(f"  ETL code: {len(artifacts.get('etl_code', '')):6d} chars")
        print(f"  DAG:      {len(artifacts.get('airflow_dag', '')):6d} chars")
        
        # Check healing efficiency
        healing = s.get('healing_history', [])
        print(f"\nHEALING:")
        print(f"  Iterations: {len(healing)}")
        for i, h in enumerate(healing, 1):
            issues = len(h.get('issues_found', []))
            print(f"    Iteration {i}: {issues} issues")
        
        readiness = s.get('readiness', {})
        print(f"  Readiness: {readiness.get('overall', 0)}/100")
        
        break
    
    time.sleep(1)

print("\n" + "=" * 60)
if 'healing' in phase_times and phase_times.get('healing', 0) < 60:
    print("✓ OPTIMIZATION SUCCESSFUL - Healing < 60s")
elif phase_times.get('healing', 0) < 120:
    print("✓ GOOD - Healing < 2 minutes")
else:
    print("⚠ Healing still taking > 2 minutes")
print("=" * 60)
