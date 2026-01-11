#!/usr/bin/env python3
"""Test OpenAI API connection"""

import os
import sys

# Check for API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not set!")
    print()
    print("Set it with:")
    print("  export OPENAI_API_KEY='sk-...'")
    print()
    print("Or get one from: https://platform.openai.com/api-keys")
    sys.exit(1)

print("✅ API Key found:", api_key[:10] + "..." + api_key[-4:])
print()

# Test connection
try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    
    print("Testing OpenAI API connection...")
    print()
    
    # Simple test
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Say 'OpenAI API is working!' if you can read this."}
        ],
        max_tokens=20
    )
    
    content = response.choices[0].message.content
    print("✅ SUCCESS! OpenAI API is working!")
    print(f"Response: {content}")
    print()
    print("You can now run the game with:")
    print("  python3 main.py --ai --api openai")
    
except ImportError:
    print("❌ OpenAI library not installed")
    print("Install with: pip3 install openai")
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Check:")
    print("  1. Your API key is correct")
    print("  2. You have credits/quota")
    print("  3. Your internet connection")
