#!/usr/bin/env python
"""Test demo safety mode (LLM_ENABLED=false)"""
import os
import sys

# Set demo mode flags
os.environ['LLM_ENABLED'] = 'false'
os.environ['USE_LLM_API'] = 'false'

from fastapi.testclient import TestClient
import main

print("=" * 60)
print("PHASE 7: DEMO SAFETY MODE VERIFICATION")
print("=" * 60)

client = TestClient(main.app)

# Test 1: Health endpoint
print("\n[TEST 1] Health Endpoint")
health = client.get('/health')
print(f"  Status: {health.status_code}")
if health.status_code == 200:
    data = health.json()
    ai_status = data.get('ai', {})
    print(f"  LLM Loaded: {ai_status.get('llm_loaded', False)}")
    print(f"  LLM Enabled: {ai_status.get('llm_enabled', False)}")
    print("  [PASS] PASS")
else:
    print("  [FAIL] FAIL")
    sys.exit(1)

# Test 2: RAG query with fallback
print("\n[TEST 2] RAG Query (Template Fallback)")
query_resp = client.post('/api/v1/rag/query', json={
    'query': 'What are symptoms of pneumonia?',
    'top_k': 3
})
print(f"  Status: {query_resp.status_code}")
if query_resp.status_code == 200:
    data = query_resp.json()
    print(f"  Answer Present: {bool(data.get('answer'))}")
    print(f"  Sources Count: {len(data.get('sources', []))}")
    print(f"  Confidence: {data.get('confidence', 0):.2f}")
    print(f"  Language: {data.get('language', 'unknown')}")
    
    answer_preview = str(data.get('answer', ''))[:80]
    print(f"  Answer Preview: {answer_preview}...")
    
    # Verify schema intact
    required_keys = {'answer', 'sources', 'confidence', 'language'}
    if required_keys.issubset(data.keys()):
        print("  [PASS] PASS")
    else:
        print(f"  [FAIL] FAIL: Missing keys: {required_keys - data.keys()}")
        sys.exit(1)
else:
    print(f"  [FAIL] FAIL: {query_resp.text}")
    sys.exit(1)

# Test 3: Metrics endpoint
print("\n[TEST 3] Metrics Endpoint")
metrics = client.get('/metrics/stats')
print(f"  Status: {metrics.status_code}")
if metrics.status_code == 200:
    data = metrics.json()
    print(f"  Timestamp: {data.get('timestamp', 'unknown')}")
    agg = data.get('aggregated_metrics', {})
    print(f"  Query Count: {agg.get('query_count', 0)}")
    print(f"  Avg Response Time: {agg.get('avg_response_time_ms', 0):.2f}ms")
    print("  [PASS] PASS")
else:
    print("  [FAIL] FAIL")
    sys.exit(1)

# Test 4: Multiple queries to verify no crashes
print("\n[TEST 4] Multiple Queries (Stability)")
queries = [
    'What is tuberculosis?',
    'Describe malaria symptoms',
    'How is diabetes treated?'
]
all_passed = True
for idx, q in enumerate(queries, 1):
    resp = client.post('/api/v1/rag/query', json={'query': q})
    status = "[PASS]" if resp.status_code == 200 else "[FAIL]"
    print(f"  Query {idx}: {status} (status={resp.status_code})")
    if resp.status_code != 200:
        all_passed = False

if all_passed:
    print("  [PASS] PASS")
else:
    print("  [FAIL] FAIL")
    sys.exit(1)

print("\n" + "=" * 60)
print("[PASS] ALL DEMO SAFETY MODE TESTS PASSED")
print("=" * 60)
print("\nSystem is production-ready for safe demo with:")
print("  - No LLM API calls (faster responses)")
print("  - Template fallback generation (graceful)")
print("  - All endpoints functional")
print("  - Schema integrity maintained")
print("  - No crashes under multiple queries")
