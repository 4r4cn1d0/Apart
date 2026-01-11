#!/usr/bin/env python3
"""
Check for inference endpoints on Lambda Labs instance.
"""

import requests
import json

# Your instance details
INSTANCE_IP = "192.222.59.32"
INSTANCE_ID = "c0bfb788ee7c4ee88c70d87172f2b960"

print("=" * 60)
print("Checking Lambda Labs Inference Endpoints")
print("=" * 60)
print()
print(f"Instance IP: {INSTANCE_IP}")
print(f"Instance ID: {INSTANCE_ID}")
print()

# Common inference endpoint patterns
endpoints_to_try = [
    f"http://{INSTANCE_IP}:8000/v1/chat/completions",
    f"http://{INSTANCE_IP}:8000/v1/completions",
    f"http://{INSTANCE_IP}:5000/v1/chat/completions",
    f"http://{INSTANCE_IP}:8080/v1/chat/completions",
    f"https://{INSTANCE_IP}/v1/chat/completions",
    f"http://{INSTANCE_IP}/v1/chat/completions",
]

print("Trying common inference endpoint patterns...")
print()

for endpoint in endpoints_to_try:
    try:
        print(f"Trying: {endpoint}")
        # Simple health check or options request
        response = requests.get(endpoint, timeout=2)
        print(f"  Status: {response.status_code}")
        if response.status_code != 404:
            print(f"  Response: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print(f"  Connection refused (no server on this endpoint)")
    except requests.exceptions.Timeout:
        print(f"  Timeout")
    except Exception as e:
        print(f"  Error: {e}")
    print()

print("=" * 60)
print("Next Steps:")
print("=" * 60)
print()
print("If none of these work, you may need to:")
print("  1. SSH into your instance and check what's running")
print("  2. Deploy an inference server (like vLLM, TGI, etc.)")
print("  3. Check Lambda Labs dashboard for inference endpoint")
print("  4. Check Lambda Spaces if you're using that")
print()
print("To SSH into your instance:")
print(f"  ssh root@{INSTANCE_IP}")
print()
