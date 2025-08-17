#!/usr/bin/env python3
"""Test script for the Gemini proxy."""

import os
import sys
import time
import requests
import subprocess
import signal
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

def test_with_proxy():
    """Test Gemini API through the proxy."""
    
    # Set proxy environment variables
    proxy_url = "http://localhost:8080"
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    
    # Also configure requests to use proxy
    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }
    
    print("Testing Gemini API through proxy...")
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Please set GEMINI_API_KEY environment variable")
        return
    
    # Test 1: List models
    print("\n=== Test 1: List Models ===")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        # Disable SSL verification for proxy testing
        response = requests.get(url, proxies=proxies, verify=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ List models successful")
        else:
            print(f"❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Generate content
    print("\n=== Test 2: Generate Content ===")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Hello! What is 2+2?"}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, proxies=proxies, verify=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Response: {text[:100]}")
            else:
                print("✅ Request successful, but no candidates in response")
        else:
            print(f"❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Multi-turn conversation
    print("\n=== Test 3: Multi-turn Conversation ===")
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "What is the capital of France?"}]
            },
            {
                "role": "model",
                "parts": [{"text": "The capital of France is Paris."}]
            },
            {
                "role": "user",
                "parts": [{"text": "What is its population?"}]
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, proxies=proxies, verify=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if "candidates" in data:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ Response: {text[:100]}")
            else:
                print("✅ Request successful")
        else:
            print(f"❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")


def test_with_sdk():
    """Test using Google's SDK through the proxy."""
    print("\n=== Testing with Google SDK ===")
    
    # Set proxy
    proxy_url = "http://localhost:8080"
    os.environ['HTTP_PROXY'] = proxy_url
    os.environ['HTTPS_PROXY'] = proxy_url
    
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("Please set GEMINI_API_KEY")
            return
        
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("What is 5+5?")
        
        print(f"✅ SDK Response: {response.text[:100]}")
        
    except Exception as e:
        print(f"❌ SDK Error: {e}")


def main():
    """Main test function."""
    print("=" * 60)
    print("Gemini Proxy Test Suite")
    print("=" * 60)
    
    # Check if proxy is running
    try:
        response = requests.get("http://localhost:8080", timeout=1)
    except:
        print("\n⚠️  Proxy not running on port 8080")
        print("Start it with: python gemini_proxy.py --debug")
        return
    
    print("\n✅ Proxy is running on port 8080")
    
    # Suppress SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Run tests
    test_with_proxy()
    test_with_sdk()
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)


if __name__ == "__main__":
    main()