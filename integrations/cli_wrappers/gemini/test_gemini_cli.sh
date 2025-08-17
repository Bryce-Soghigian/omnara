#!/bin/bash
# Test script for Gemini CLI behavior

echo "=== Testing Gemini CLI ==="

# Check if gemini CLI is available
if ! command -v gemini &> /dev/null; then
    echo "Gemini CLI not found. Please install with: brew install gemini-cli"
    exit 1
fi

echo "Gemini CLI found at: $(which gemini)"
echo ""

# Test help command
echo "=== Gemini Help ==="
gemini --help
echo ""

# Test version
echo "=== Gemini Version ==="
gemini --version 2>/dev/null || echo "No version flag"
echo ""

# Check config location
echo "=== Checking for config ==="
if [ -f "$HOME/.gemini/config.json" ]; then
    echo "Config found at: $HOME/.gemini/config.json"
    cat "$HOME/.gemini/config.json"
else
    echo "No config file found"
fi
echo ""

# Test basic prompt (will fail without API key)
echo "=== Testing basic prompt (may fail without API key) ==="
echo "Hello, can you help me?" | gemini 2>&1 | head -20
echo ""

echo "=== Testing with environment variable ==="
if [ -n "$GEMINI_API_KEY" ]; then
    echo "Testing with GEMINI_API_KEY set"
    echo "What is 2+2?" | gemini 2>&1
else
    echo "GEMINI_API_KEY not set"
fi