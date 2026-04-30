#!/usr/bin/env python
"""Quick test to reproduce and debug the backend 500 error."""

import sys
import os

# Add repo root to path
ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import httpx
    
    payload = {
        "session_id": "test_session_001",
        "message": "what are the risks of my portfolio",
        "portfolio_id": "PORTFOLIO_001"
    }
    
    print("=" * 60)
    print("Testing non-streaming endpoint...")
    print("=" * 60)
    print(f"Payload: {payload}")
    print()
    
    r = httpx.post(
        "http://127.0.0.1:8000/api/v1/chat",
        json=payload,
        timeout=60
    )
    
    print(f"Status: {r.status_code}")
    print(f"Response:\n{r.text}")
    print()
    
except Exception as e:
    print(f"Test script error: {e}")
    import traceback
    traceback.print_exc()
