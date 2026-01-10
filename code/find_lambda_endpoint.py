#!/usr/bin/env python3
"""
Script to find your Lambda Labs model instance endpoint.
"""

import os
import requests
import json

def find_instances():
    """List your Lambda Labs instances to find the inference endpoint."""
    
    api_key = os.getenv("LAMBDA_API_KEY", "secret_apart_58f182d70df5470086566cbd9ceccbc7.B7VkBa9N4KDNbxnNxxSt9uwHnx5FxSDY")
    base_url = "https://cloud.lambda.ai/api/v1"
    
    print("=" * 60)
    print("Finding Lambda Labs Model Instances")
    print("=" * 60)
    print()
    
    # Try to list instances
    instances_url = f"{base_url}/instances"
    auth = (api_key, "")
    
    print(f"Checking instances at: {instances_url}")
    print()
    
    try:
        response = requests.get(instances_url, auth=auth, timeout=30)
        print(f"Response Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            instances = response.json()
            print("✅ Found instances!")
            print()
            print(json.dumps(instances, indent=2))
            print()
            
            # Try to extract endpoint information
            if isinstance(instances, list) and len(instances) > 0:
                print("=" * 60)
                print("Instance Details:")
                print("=" * 60)
                for i, instance in enumerate(instances):
                    print(f"\nInstance {i+1}:")
                    if isinstance(instance, dict):
                        for key, value in instance.items():
                            if 'endpoint' in key.lower() or 'url' in key.lower() or 'host' in key.lower():
                                print(f"  {key}: {value}")
                            elif key == 'id' or key == 'name':
                                print(f"  {key}: {value}")
            
        else:
            print(f"Response: {response.text}")
            print()
            print("This might mean:")
            print("  1. You need to deploy a model instance first")
            print("  2. The API structure is different")
            print("  3. Check Lambda Labs dashboard for instance endpoints")
            
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Please check:")
        print("  1. Your Lambda Labs dashboard for deployed instances")
        print("  2. The instance endpoint URL (usually shown in the dashboard)")
        print("  3. Lambda Labs documentation: https://docs.lambda.ai/api/cloud")

if __name__ == "__main__":
    find_instances()
