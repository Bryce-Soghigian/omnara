#!/usr/bin/env python3
"""Setup script for Gemini provider dependencies."""

import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """Install required dependencies for Gemini provider."""
    dependencies = [
        "aiohttp>=3.8.0",
        "requests>=2.25.0",
        "google-generativeai>=0.8.0",
    ]
    
    print("Installing Gemini provider dependencies...")
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", dep
            ])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    print("\n✅ All dependencies installed successfully!")
    return True

def check_gemini_cli():
    """Check if Gemini CLI is available."""
    try:
        result = subprocess.run(
            ["gemini", "--version"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Gemini CLI found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Gemini CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ Gemini CLI not found")
        print("Install with: brew install gemini-cli")
        return False

def main():
    """Main setup function."""
    print("=" * 60)
    print("Gemini Provider Setup")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check Gemini CLI
    check_gemini_cli()
    
    print("\n" + "=" * 60)
    print("Setup complete! You can now use:")
    print("  omnara --agent=gemini")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)