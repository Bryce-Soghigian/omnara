#!/usr/bin/env python3
"""Simple test to understand Gemini API structure without API key."""

import json
import sys

# Test data structures based on Gemini API documentation
def test_request_structure():
    """Show expected Gemini API request structure."""
    
    # Basic request
    basic_request = {
        "contents": [
            {
                "parts": [
                    {"text": "Hello, how are you?"}
                ],
                "role": "user"  # Optional for first message
            }
        ]
    }
    
    print("=== Basic Request Structure ===")
    print(json.dumps(basic_request, indent=2))
    
    # Multi-turn conversation
    conversation_request = {
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
                "parts": [{"text": "Tell me more about it."}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }
    
    print("\n=== Multi-turn Conversation Request ===")
    print(json.dumps(conversation_request, indent=2))
    
    # Expected response structure
    expected_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Response text here..."}
                    ],
                    "role": "model"
                },
                "finishReason": "STOP",
                "index": 0,
                "safetyRatings": [
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "probability": "NEGLIGIBLE"
                    }
                ]
            }
        ],
        "promptFeedback": {
            "safetyRatings": []
        }
    }
    
    print("\n=== Expected Response Structure ===")
    print(json.dumps(expected_response, indent=2))


def test_api_endpoints():
    """Show Gemini API endpoints."""
    
    base_url = "https://generativelanguage.googleapis.com"
    
    endpoints = {
        "List Models": f"{base_url}/v1beta/models",
        "Generate Content": f"{base_url}/v1beta/models/gemini-pro:generateContent",
        "Stream Generate": f"{base_url}/v1beta/models/gemini-pro:streamGenerateContent",
        "Count Tokens": f"{base_url}/v1beta/models/gemini-pro:countTokens",
        "Embed Content": f"{base_url}/v1beta/models/embedding-001:embedContent",
    }
    
    print("\n=== Gemini API Endpoints ===")
    for name, endpoint in endpoints.items():
        print(f"{name}: {endpoint}")
    
    print("\nNote: All endpoints require ?key=YOUR_API_KEY parameter")


def test_proxy_requirements():
    """Define what our proxy needs to intercept."""
    
    print("\n=== Proxy Requirements ===")
    
    requirements = {
        "Intercept Requests": [
            "Extract prompt from contents[].parts[].text",
            "Capture generation config",
            "Track conversation history",
            "Identify user vs model roles"
        ],
        "Intercept Responses": [
            "Extract response from candidates[].content.parts[].text",
            "Handle streaming responses (multiple JSON objects)",
            "Track finish reasons",
            "Monitor safety ratings"
        ],
        "Session Management": [
            "Track conversation context",
            "Maintain message history",
            "Associate with Omnara session"
        ],
        "Integration Points": [
            "Send user messages to Omnara",
            "Send model responses to Omnara",
            "Handle web UI input injection",
            "Support git diff tracking"
        ]
    }
    
    for category, items in requirements.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")


if __name__ == "__main__":
    test_request_structure()
    test_api_endpoints()
    test_proxy_requirements()