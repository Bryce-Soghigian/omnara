#!/usr/bin/env python3
"""Authentication helper for Gemini CLI."""

import subprocess


def check_gemini_auth():
    """Check if Gemini CLI is authenticated."""
    try:
        # Try to run a simple command to test auth
        result = subprocess.run(
            ["gemini", "--version"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def setup_gemini_auth():
    """Help user set up Gemini authentication."""
    print("🔐 Setting up Gemini Authentication")
    print("=" * 50)

    print("\n📋 Gemini CLI supports multiple authentication methods:")
    print("\n1. 🌐 Google Account (Interactive Login)")
    print("   - Gemini CLI will open your browser")
    print("   - Sign in with your Google account")
    print("   - Free tier available")

    print("\n2. 🔑 API Key (Direct)")
    print("   - Get API key from: https://makersuite.google.com/app/apikey")
    print("   - Set GEMINI_API_KEY environment variable")

    print("\n3. 🔧 gcloud CLI (Service Account)")
    print("   - Use: gcloud auth application-default login")
    print("   - For programmatic access")

    print("\n" + "=" * 50)
    print("💡 Recommendation: Try option 1 (Google Account) first")
    print("   It's the easiest and includes free usage!")

    choice = input("\nWhich method would you like to try? (1/2/3): ").strip()

    if choice == "1":
        print("\n🚀 Launching Gemini CLI for authentication...")
        print("   Follow the browser prompts to sign in")
        try:
            subprocess.run(["gemini"], check=False)
        except KeyboardInterrupt:
            print("\n✅ Authentication setup interrupted")

    elif choice == "2":
        print("\n🔑 API Key Setup:")
        print("1. Visit: https://makersuite.google.com/app/apikey")
        print("2. Create or copy your API key")
        print("3. Set it as an environment variable:")
        print("   export GEMINI_API_KEY='your_api_key_here'")
        print("4. Restart your terminal and try again")

    elif choice == "3":
        print("\n🔧 gcloud CLI Setup:")
        print("1. Install gcloud CLI if needed")
        print("2. Run: gcloud auth application-default login")
        print("3. Follow the browser prompts")
        try:
            subprocess.run(
                ["gcloud", "auth", "application-default", "login"], check=False
            )
        except FileNotFoundError:
            print("❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk")

    else:
        print("❌ Invalid choice. Please run this script again.")


def main():
    """Main function."""
    print("🔍 Checking Gemini CLI authentication...")

    if check_gemini_auth():
        print("✅ Gemini CLI is authenticated and working!")
        return

    print("❌ Gemini CLI needs authentication")
    setup_gemini_auth()


if __name__ == "__main__":
    main()
