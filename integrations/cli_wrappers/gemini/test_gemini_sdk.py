#!/usr/bin/env python3
"""Test Gemini SDK to understand its behavior for our wrapper."""

import os
import google.generativeai as genai
from typing import Optional
import json
import time

# Configure with API key
API_KEY = os.environ.get("GEMINI_API_KEY", "")


def test_basic_generation():
    """Test basic text generation."""
    print("\n=== Testing Basic Generation with SDK ===")
    
    if not API_KEY:
        print("Please set GEMINI_API_KEY environment variable")
        return
    
    genai.configure(api_key=API_KEY)
    
    # Create model
    model = genai.GenerativeModel('gemini-pro')
    
    # Generate content
    response = model.generate_content("Hello! Tell me a bit about yourself in 2-3 sentences.")
    
    print(f"Response text: {response.text}")
    print(f"Response object type: {type(response)}")
    print(f"Response attributes: {dir(response)}")
    
    # Check for candidates
    if hasattr(response, 'candidates'):
        print(f"Number of candidates: {len(response.candidates)}")
        for i, candidate in enumerate(response.candidates):
            print(f"Candidate {i}: {candidate}")


def test_streaming():
    """Test streaming responses."""
    print("\n=== Testing Streaming with SDK ===")
    
    if not API_KEY:
        return
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    # Stream response
    response = model.generate_content("Write a haiku about coding", stream=True)
    
    full_text = ""
    for chunk in response:
        print(f"Chunk: {chunk.text}")
        full_text += chunk.text
        time.sleep(0.1)  # Simulate processing
    
    print(f"\nFull response: {full_text}")


def test_chat_session():
    """Test multi-turn chat."""
    print("\n=== Testing Chat Session ===")
    
    if not API_KEY:
        return
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    # Start chat
    chat = model.start_chat(history=[])
    
    # First message
    response = chat.send_message("What's the capital of France?")
    print(f"User: What's the capital of France?")
    print(f"Assistant: {response.text}")
    
    # Follow-up
    response = chat.send_message("What's its population?")
    print(f"User: What's its population?")
    print(f"Assistant: {response.text}")
    
    # Check chat history
    print("\nChat History:")
    for message in chat.history:
        print(f"  Role: {message.role}, Content: {message.parts[0].text[:100]}...")


def test_with_generation_config():
    """Test with custom generation config."""
    print("\n=== Testing Generation Config ===")
    
    if not API_KEY:
        return
    
    genai.configure(api_key=API_KEY)
    
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 50,
    }
    
    model = genai.GenerativeModel(
        'gemini-pro',
        generation_config=generation_config
    )
    
    response = model.generate_content("Generate 3 random words")
    print(f"Response with config: {response.text}")


def test_list_models():
    """List available models."""
    print("\n=== Available Models ===")
    
    if not API_KEY:
        return
    
    genai.configure(api_key=API_KEY)
    
    for model in genai.list_models():
        print(f"Model: {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Supported methods: {model.supported_generation_methods}")
        print()


if __name__ == "__main__":
    test_list_models()
    test_basic_generation()
    test_streaming()
    test_chat_session()
    test_with_generation_config()