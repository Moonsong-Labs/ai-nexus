#!/usr/bin/env python3
"""Test script for GitHub Event Listener webhook endpoints.

This script provides easy testing of various webhook events using curl commands.
"""

import json
import subprocess
import sys


def run_curl(event_type: str, payload: dict, delivery_id: str = None):
    """Run a curl command to test webhook endpoint."""
    if delivery_id is None:
        delivery_id = (
            f"test-{event_type}-{hash(json.dumps(payload, sort_keys=True)) % 10000}"
        )

    cmd = [
        "curl",
        "-X",
        "POST",
        "http://localhost:8000/github/events",
        "-H",
        "Content-Type: application/json",
        "-H",
        f"X-GitHub-Event: {event_type}",
        "-H",
        f"X-GitHub-Delivery: {delivery_id}",
        "-d",
        json.dumps(payload, indent=2),
    ]

    print(f"\n🚀 Testing {event_type} event...")
    print(f"Delivery ID: {delivery_id}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        print("Response:")
        if result.stdout:
            try:
                response = json.loads(result.stdout)
                print(json.dumps(response, indent=2))
            except json.JSONDecodeError:
                print(result.stdout)

        if result.stderr:
            print(f"\nError: {result.stderr}")

        print(f"\nStatus Code: {result.returncode}")

    except Exception as e:
        print(f"Error running curl: {e}")


def test_ping():
    """Test ping event."""
    payload = {"zen": "Design for failure."}
    run_curl("ping", payload)


def test_issue_assigned():
    """Test issue assigned to AI bot."""
    payload = {
        "action": "assigned",
        "issue": {
            "id": 987654321,
            "number": 123,
            "title": "Fix authentication bug in login flow",
            "body": "Users are reporting login issues with GitHub OAuth.\n\n## Steps to reproduce\n1. Go to login page\n2. Click 'Login with GitHub'\n3. Authorize the app\n4. Get redirected to error page\n\n## Expected: User logged in\n## Actual: Error: 'Invalid state parameter'",
            "html_url": "https://github.com/test-org/test-repo/issues/123",
            "state": "open",
            "user": {"login": "bug-reporter", "id": 123456, "type": "User"},
            "assignee": {"login": "ai-nexus[bot]", "id": 987654321, "type": "Bot"},
            "labels": [
                {"name": "bug", "color": "d73a4a"},
                {"name": "priority:high", "color": "ff6b6b"},
            ],
            "created_at": "2024-01-10T09:00:00Z",
        },
        "repository": {
            "id": 456789012,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
            "default_branch": "main",
        },
        "sender": {"login": "project-manager", "id": 555555, "type": "User"},
    }
    run_curl("issues", payload)


def test_issue_assigned_different_user():
    """Test issue assigned to a regular user (should be skipped)."""
    payload = {
        "action": "assigned",
        "issue": {
            "id": 987654322,
            "number": 124,
            "title": "Feature request: Add dark mode",
            "body": "It would be great to have a dark mode toggle in the settings.",
            "html_url": "https://github.com/test-org/test-repo/issues/124",
            "state": "open",
            "user": {"login": "feature-requester", "id": 123457, "type": "User"},
            "assignee": {"login": "developer123", "id": 987654322, "type": "User"},
            "labels": [{"name": "enhancement", "color": "a2eeef"}],
            "created_at": "2024-01-10T10:00:00Z",
        },
        "repository": {
            "id": 456789012,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
            "default_branch": "main",
        },
        "sender": {"login": "project-manager", "id": 555555, "type": "User"},
    }
    run_curl("issues", payload)


def test_comment_trigger():
    """Test comment with AI bot trigger phrase (should be processed)."""
    payload = {
        "action": "created",
        "issue": {
            "id": 987654323,
            "number": 125,
            "title": "Authentication bug in login flow",
            "body": "Users are experiencing issues with the login system. The OAuth flow seems to be broken.",
            "html_url": "https://github.com/test-org/test-repo/issues/125",
            "state": "open",
            "user": {"login": "bug-reporter", "id": 123456, "type": "User"},
            "labels": [{"name": "bug", "color": "d73a4a"}],
            "created_at": "2024-01-10T11:00:00Z",
        },
        "comment": {
            "id": 1234567890,
            "body": "@ai-nexus-bot please help analyze this authentication issue and provide a solution",
            "html_url": "https://github.com/test-org/test-repo/issues/125#issuecomment-1234567890",
            "user": {"login": "developer456", "id": 654321, "type": "User"},
            "created_at": "2024-01-10T11:30:00Z",
        },
        "repository": {
            "id": 456789012,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
            "default_branch": "main",
        },
        "sender": {"login": "developer456", "id": 654321, "type": "User"},
    }
    run_curl("issue_comment", payload)


def test_comment_no_trigger():
    """Test comment without trigger phrase (should be skipped)."""
    payload = {
        "action": "created",
        "issue": {
            "id": 987654324,
            "number": 126,
            "title": "Documentation update needed",
            "body": "The README needs to be updated with installation instructions.",
            "html_url": "https://github.com/test-org/test-repo/issues/126",
            "state": "open",
            "user": {"login": "docs-maintainer", "id": 789012, "type": "User"},
            "labels": [{"name": "documentation", "color": "0075ca"}],
            "created_at": "2024-01-10T12:00:00Z",
        },
        "comment": {
            "id": 1234567891,
            "body": "I agree, this documentation really needs an update. We should use AI to help with this, but let me work on this manually for now.",
            "html_url": "https://github.com/test-org/test-repo/issues/126#issuecomment-1234567891",
            "user": {"login": "contributor123", "id": 345678, "type": "User"},
            "created_at": "2024-01-10T12:15:00Z",
        },
        "repository": {
            "id": 456789012,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
            "default_branch": "main",
        },
        "sender": {"login": "contributor123", "id": 345678, "type": "User"},
    }
    run_curl("issue_comment", payload)


def test_comment_partial_mention():
    """Test comment with partial bot name mention (should be skipped)."""
    payload = {
        "action": "created",
        "issue": {
            "id": 987654325,
            "number": 127,
            "title": "Performance optimization needed",
            "body": "The application is running slowly and needs optimization.",
            "html_url": "https://github.com/test-org/test-repo/issues/127",
            "state": "open",
            "user": {"login": "performance-tester", "id": 567890, "type": "User"},
            "labels": [{"name": "performance", "color": "ff9800"}],
            "created_at": "2024-01-10T13:00:00Z",
        },
        "comment": {
            "id": 1234567892,
            "body": "We could use an AI solution like nexus or another tool to analyze this. What do you think about using artificial intelligence?",
            "html_url": "https://github.com/test-org/test-repo/issues/127#issuecomment-1234567892",
            "user": {"login": "optimizer123", "id": 456789, "type": "User"},
            "created_at": "2024-01-10T13:15:00Z",
        },
        "repository": {
            "id": 456789012,
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
            "default_branch": "main",
        },
        "sender": {"login": "optimizer123", "id": 456789, "type": "User"},
    }
    run_curl("issue_comment", payload)


def test_unsupported_event():
    """Test an unsupported event type."""
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "id": 1234567890,
            "number": 42,
            "title": "Add OAuth2 authentication",
            "body": "This PR implements OAuth2 authentication.",
            "html_url": "https://github.com/test-org/test-repo/pull/42",
            "user": {"login": "developer123"},
            "base": {"ref": "main"},
            "head": {"ref": "feature/oauth-auth"},
        },
        "repository": {
            "name": "test-repo",
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
        },
    }
    run_curl("pull_request", payload)


def test_health_checks():
    """Test health check endpoints."""
    endpoints = ["/health", "/health/github", "/health/orchestrator"]

    for endpoint in endpoints:
        print(f"\n💚 Testing health check: {endpoint}")
        print("-" * 50)

        cmd = ["curl", f"http://localhost:8000{endpoint}"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                try:
                    response = json.loads(result.stdout)
                    print(json.dumps(response, indent=2))
                except json.JSONDecodeError:
                    print(result.stdout)

            if result.stderr:
                print(f"Error: {result.stderr}")

        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main test function."""
    print("🔧 GitHub Event Listener Test Script")
    print("=" * 50)
    print("Testing functionality: Issue assignments and comment triggers")
    print("\nMake sure the service is running:")
    print("uvicorn src.event_listener.server:app --reload --port 8000")
    print()

    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()

        tests = {
            "ping": test_ping,
            "assigned": test_issue_assigned,
            "issue": test_issue_assigned,
            "skip": test_issue_assigned_different_user,
            "comment": test_comment_trigger,
            "comment-no-trigger": test_comment_no_trigger,
            "comment-partial": test_comment_partial_mention,
            "unsupported": test_unsupported_event,
            "health": test_health_checks,
            "all": lambda: [
                test_ping(),
                test_issue_assigned(),
                test_issue_assigned_different_user(),
                test_comment_trigger(),
                test_comment_no_trigger(),
                test_comment_partial_mention(),
                test_unsupported_event(),
            ],
        }

        if test_type in tests:
            tests[test_type]()
        else:
            print(f"Unknown test type: {test_type}")
            print(f"Available tests: {', '.join(tests.keys())}")
    else:
        print("Usage: python scripts/test_webhooks.py <test_type>")
        print("\nAvailable tests:")
        print("  ping              - Test ping event")
        print("  assigned          - Test issue assigned to AI bot (supported)")
        print(
            "  skip              - Test issue assigned to regular user (should be skipped)"
        )
        print(
            "  comment           - Test comment with AI bot trigger phrase (supported)"
        )
        print(
            "  comment-no-trigger - Test comment without trigger phrase (should be skipped)"
        )
        print(
            "  comment-partial   - Test comment with partial bot name (should be skipped)"
        )
        print("  unsupported       - Test unsupported event type (PR opened)")
        print("  health            - Test health check endpoints")
        print("  all               - Run all tests")
        print("\nExample: python scripts/test_webhooks.py comment")
        print(
            "\nNote: This service processes issue assignments and comments with explicit bot mentions."
        )
        print(
            "Required mentions: ai-nexus-bot, @ai-nexus-bot (exact full name required)"
        )


if __name__ == "__main__":
    main()
