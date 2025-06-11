#!/usr/bin/env python3
"""
Setup script for GitHub App configuration.

This script helps users configure their GitHub App for the Event Listener service.
It provides guidance on creating the app and extracting necessary configuration values.
"""

import base64
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_step(number: int, text: str):
    """Print a numbered step."""
    print(f"\n{number}. {text}")
    print("-" * 40)


def check_env_file():
    """Check if .env file exists and create from example if not."""
    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if not env_path.exists():
        if env_example_path.exists():
            print("Creating .env file from .env.example...")
            env_example_path.rename(env_path)
        else:
            print("ERROR: Neither .env nor .env.example found!")
            return False

    return True


def get_current_config():
    """Read current configuration from .env file."""
    config = {}
    env_path = Path(".env")

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip().strip('"')

    return config


def update_env_file(key: str, value: str):
    """Update a specific key in the .env file."""
    env_path = Path(".env")
    lines = []

    with open(env_path) as f:
        lines = f.readlines()

    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}="):
            lines[i] = f'{key}="{value}"\n'
            updated = True
            break

    if not updated:
        lines.append(f'{key}="{value}"\n')

    with open(env_path, "w") as f:
        f.writelines(lines)


def validate_private_key(key_path: str) -> bool:
    """Validate that the private key file exists and is readable."""
    path = Path(key_path)
    if not path.exists():
        print(f"ERROR: Private key file not found: {key_path}")
        return False

    try:
        with open(path) as f:
            content = f.read()
            if "BEGIN RSA PRIVATE KEY" not in content:
                print("ERROR: File doesn't appear to be a valid RSA private key")
                return False
        return True
    except Exception as e:
        print(f"ERROR: Cannot read private key file: {e}")
        return False


def test_webhook_endpoint():
    """Test if the webhook endpoint is accessible."""
    try:
        import requests

        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✓ Event Listener service is running")
            return True
        else:
            print("✗ Event Listener service returned error")
            return False
    except:
        print("✗ Event Listener service is not running")
        print("  Start it with: uvicorn src.event_listener.server:app --reload")
        return False


def main():
    """Main setup flow."""
    print_header("GitHub App Setup for Event Listener")

    # Check environment
    if not check_env_file():
        return 1

    config = get_current_config()

    print(
        "This script will help you configure your GitHub App for the Event Listener.\n"
    )
    print("Current configuration:")
    print(f"  GITHUB_APP_ID: {config.get('GITHUB_APP_ID', 'Not set')}")
    print(
        f"  GITHUB_INSTALLATION_ID: {config.get('GITHUB_INSTALLATION_ID', 'Not set')}"
    )
    print(
        f"  GITHUB_WEBHOOK_SECRET: {'Set' if config.get('GITHUB_WEBHOOK_SECRET') else 'Not set'}"
    )

    # Step 1: Create GitHub App
    print_step(1, "Create a GitHub App")
    print("Go to: https://github.com/settings/apps/new")
    print("\nUse these settings:")
    print("  Name: AI Nexus Event Listener (or your choice)")
    print("  Homepage URL: http://localhost:8000")
    print("  Webhook URL: http://your-domain:8000/github/events")
    print("    (Use ngrok for testing: ngrok http 8000)")
    print("  Webhook secret: Generate a random string")
    print("\nPermissions needed:")
    print("  Repository permissions:")
    print("    - Contents: Read")
    print("    - Issues: Read & Write")
    print("    - Pull requests: Read & Write")
    print("    - Actions: Read (optional)")
    print("  Subscribe to events:")
    print("    - Issues")
    print("    - Issue comment")
    print("    - Pull request")
    print("    - Pull request review")
    print("    - Pull request review comment")
    print("    - Push")

    input("\nPress Enter when you've created the GitHub App...")

    # Step 2: Get App ID
    print_step(2, "Enter GitHub App ID")
    app_id = input("GitHub App ID (from app settings): ").strip()
    if app_id:
        update_env_file("GITHUB_APP_ID", app_id)
        print(f"✓ Updated GITHUB_APP_ID to {app_id}")

    # Step 3: Get Installation ID
    print_step(3, "Install the App and Get Installation ID")
    print("1. Go to your app settings")
    print("2. Click 'Install App' and choose repositories")
    print("3. After installation, look at the URL:")
    print("   https://github.com/settings/installations/XXXXXXXX")
    print("   The XXXXXXXX is your installation ID")
    print("\nAlternatively, check 'Advanced' tab > 'Recent Deliveries'")
    print("The installation ID is in the payload")

    installation_id = input("\nGitHub Installation ID: ").strip()
    if installation_id:
        update_env_file("GITHUB_INSTALLATION_ID", installation_id)
        print(f"✓ Updated GITHUB_INSTALLATION_ID to {installation_id}")

    # Step 4: Set up webhook secret
    print_step(4, "Configure Webhook Secret")
    print("The webhook secret should match what you set in GitHub App settings")

    webhook_secret = input("Webhook secret: ").strip()
    if webhook_secret:
        update_env_file("GITHUB_WEBHOOK_SECRET", webhook_secret)
        print("✓ Updated GITHUB_WEBHOOK_SECRET")

    # Step 5: Private key
    print_step(5, "Configure Private Key")
    print("1. In your GitHub App settings, generate a private key")
    print("2. Save the downloaded .pem file")
    print("3. You can either:")
    print("   a) Provide the path to the .pem file")
    print("   b) Copy the key content to GITHUB_APP_PRIVATE_KEY")

    key_choice = input(
        "\nEnter path to private key file (or press Enter to skip): "
    ).strip()
    if key_choice:
        if validate_private_key(key_choice):
            # Read the key content
            with open(key_choice) as f:
                key_content = f.read()
            update_env_file("GITHUB_APP_PRIVATE_KEY", key_content)
            print("✓ Updated GITHUB_APP_PRIVATE_KEY")

    # Step 6: Test configuration
    print_step(6, "Test Configuration")
    print("Configuration complete! Here's how to test:")
    print("\n1. Start the Event Listener service:")
    print("   uvicorn src.event_listener.server:app --reload")
    print("\n2. Expose to internet (for webhooks):")
    print("   ngrok http 8000")
    print("\n3. Update webhook URL in GitHub App settings with ngrok URL")
    print("\n4. Test with a ping:")
    print("   Go to GitHub App settings > Advanced > Recent Deliveries")
    print("   Click 'Redeliver' on any ping event")

    # Test local endpoint
    print("\nTesting local endpoint...")
    test_webhook_endpoint()

    print_header("Setup Complete!")
    print("Your GitHub App is configured for the Event Listener.")
    print("\nNext steps:")
    print("1. Start the service: uvicorn src.event_listener.server:app --reload")
    print("2. Create a test issue or PR in your repository")
    print("3. Check the service logs to see event processing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
