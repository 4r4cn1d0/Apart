#!/usr/bin/env python3
"""
Helper script to test and configure Lambda Labs API integration.
Run this to verify your Lambda Labs API setup.
"""

import os
import requests
import json

def test_lambda_api():
    """Test Lambda Labs API connection and get configuration details."""
    
    print("=" * 60)
    print("Lambda Labs API Configuration Helper")
    print("=" * 60)
    print()
    
    # Get API key
    api_key = os.getenv("LAMBDA_API_KEY")
    if not api_key:
        api_key = input("Enter your Lambda Labs API key: ").strip()
        if not api_key:
            print("❌ API key is required!")
            return
    
    print(f"✓ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print()
    
    # Get API endpoint
    print("What is your Lambda Labs API base URL?")
    print("Common formats:")
    print("  - https://cloud.lambda.ai/api/v1 (for cloud.lambda.ai)")
    print("  - https://api.lambdalabs.com/v1 (alternative)")
    print("  - Custom base URL")
    print()
    
    base_url = os.getenv("LAMBDA_API_URL")
    if not base_url:
        base_url = input("Enter API base URL (or press Enter for default): ").strip()
        if not base_url:
            base_url = "https://cloud.lambda.ai/api/v1"
            print(f"Using default: {base_url}")
    else:
        print(f"Using from environment: {base_url}")
    
    # Construct full endpoint URL
    api_url = f"{base_url}/chat/completions"
    
    print()
    
    # Get model name
    print("What model do you want to use?")
    print("Common vision models:")
    print("  - llama-3.1-70b-vision-instruct")
    print("  - llama-3.1-8b-vision-instruct")
    print("  - Or your specific model name")
    print()
    
    model = os.getenv("LAMBDA_MODEL")
    if not model:
        model = input("Enter model name (or press Enter for default): ").strip()
        if not model:
            model = "llama-3.1-70b-vision-instruct"
            print(f"Using default: {model}")
    else:
        print(f"Using from environment: {model}")
    
    print()
    print("=" * 60)
    print("Testing API Connection...")
    print("=" * 60)
    print()
    
    # Test API call
    # Lambda Labs uses HTTP Basic Auth (API key as username, empty password)
    headers = {
        "Content-Type": "application/json"
    }
    auth = (api_key, "")  # HTTP Basic Auth
    
    # Simple test payload
    test_payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello, Lambda Labs API is working!' if you can read this."
            }
        ],
        "max_tokens": 50
    }
    
    try:
        print(f"Making test request to: {api_url}")
        print(f"Using model: {model}")
        print(f"Using HTTP Basic Auth (API key as username)")
        print()
        
        response = requests.post(api_url, headers=headers, json=test_payload, auth=auth, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print()
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ SUCCESS! API is working correctly.")
            print()
            print("Response structure:")
            print(json.dumps(response_data, indent=2))
            print()
            
            # Extract response content
            if "choices" in response_data:
                content = response_data["choices"][0]["message"]["content"]
                print(f"Model response: {content}")
            elif "content" in response_data:
                print(f"Model response: {response_data['content']}")
            
            print()
            print("=" * 60)
            print("Configuration Summary")
            print("=" * 60)
            print()
            print("Add these to your environment or use them in the game:")
            print()
            print(f"export LAMBDA_API_KEY=\"{api_key}\"")
            print(f"export LAMBDA_API_URL=\"{api_url}\"")
            print(f"export LAMBDA_MODEL=\"{model}\"")
            print()
            print("Then run the game with:")
            print("  python3 main.py --ai --api lambda")
            print()
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            print()
            print("Common issues:")
            print("  1. Check if your API key is correct")
            print("  2. Verify the endpoint URL is correct")
            print("  3. Make sure the model name is available on your account")
            print("  4. Check if you have credits/quota remaining")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
        print()
        print("Possible issues:")
        print("  1. Network connection problem")
        print("  2. Incorrect API endpoint URL")
        print("  3. API service might be down")
        print()
        print("Please check:")
        print("  - Your internet connection")
        print("  - Lambda Labs API status page")
        print("  - The endpoint URL format")

if __name__ == "__main__":
    try:
        test_lambda_api()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
