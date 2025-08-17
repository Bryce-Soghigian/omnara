#!/usr/bin/env python3
"""Test script to explore Gemini API requests and responses.

This script helps us understand:
1. How to make requests to Gemini API
2. What the request/response format looks like
3. How streaming works
4. What we need to intercept for the proxy
"""

import os
import json
import requests
from typing import Dict, Any, Optional
import time

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com"


def test_list_models():
    """Test listing available Gemini models."""
    print("\n=== Testing List Models ===")
    
    url = f"{GEMINI_API_BASE}/v1beta/models?key={GEMINI_API_KEY}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Available Models:")
            for model in data.get("models", []):
                print(f"  - {model.get('name')}: {model.get('displayName')}")
                print(f"    Supported methods: {model.get('supportedGenerationMethods', [])}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")


def test_generate_content():
    """Test basic content generation."""
    print("\n=== Testing Generate Content ===")
    
    model = "gemini-pro"
    url = f"{GEMINI_API_BASE}/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    # Request payload
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Hello! Can you tell me a bit about yourself?"
                    }
                ]
            }
        ]
    }
    
    print(f"Request URL: {url}")
    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse Structure:")
            print(json.dumps(data, indent=2))
            
            # Extract the actual text response
            if "candidates" in data and data["candidates"]:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    print(f"\nExtracted Text Response:\n{text}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")


def test_streaming_generation():
    """Test streaming content generation."""
    print("\n=== Testing Streaming Generation ===")
    
    model = "gemini-pro"
    url = f"{GEMINI_API_BASE}/v1beta/models/{model}:streamGenerateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Write a short poem about coding"
                    }
                ]
            }
        ]
    }
    
    print(f"Request URL: {url}")
    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, stream=True)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\nStreaming Response Chunks:")
            full_text = ""
            
            for line in response.iter_lines():
                if line:
                    # Parse the JSON chunk
                    try:
                        chunk_str = line.decode('utf-8')
                        # Remove 'data: ' prefix if present
                        if chunk_str.startswith('data: '):
                            chunk_str = chunk_str[6:]
                        
                        chunk = json.loads(chunk_str)
                        print(f"\nChunk: {json.dumps(chunk, indent=2)}")
                        
                        # Extract text from chunk
                        if "candidates" in chunk and chunk["candidates"]:
                            candidate = chunk["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                text = candidate["content"]["parts"][0].get("text", "")
                                full_text += text
                                
                    except json.JSONDecodeError as e:
                        print(f"Could not decode chunk: {line}")
                        
            print(f"\nFull Generated Text:\n{full_text}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")


def test_multi_turn_conversation():
    """Test multi-turn conversation."""
    print("\n=== Testing Multi-turn Conversation ===")
    
    model = "gemini-pro"
    url = f"{GEMINI_API_BASE}/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    # Multi-turn conversation
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "What is the capital of France?"}
                ]
            },
            {
                "role": "model",
                "parts": [
                    {"text": "The capital of France is Paris."}
                ]
            },
            {
                "role": "user",
                "parts": [
                    {"text": "What is its population?"}
                ]
            }
        ]
    }
    
    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")


def test_with_generation_config():
    """Test with generation configuration."""
    print("\n=== Testing with Generation Config ===")
    
    model = "gemini-pro"
    url = f"{GEMINI_API_BASE}/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": "Generate exactly 3 random words"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "topK": 1,
            "topP": 1,
            "maxOutputTokens": 20,
            "stopSequences": []
        }
    }
    
    print(f"Request Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse: {json.dumps(data, indent=2)}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")


def main():
    """Run all tests."""
    if not GEMINI_API_KEY:
        print("ERROR: Please set GEMINI_API_KEY environment variable")
        print("You can get an API key from: https://makersuite.google.com/app/apikey")
        return
    
    print(f"Using API Key: {GEMINI_API_KEY[:10]}...")
    
    # Run tests
    test_list_models()
    test_generate_content()
    test_streaming_generation()
    test_multi_turn_conversation()
    test_with_generation_config()


if __name__ == "__main__":
    main()