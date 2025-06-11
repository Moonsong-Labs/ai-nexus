"""Tests for event processor module."""

import json
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from event_listener.event_processor import EventProcessor, get_event_processor
from orchestrator.state import State


class TestEventProcessor:
    """Test event processor functionality."""

    @pytest.fixture
    def processor(self):
        """Create event processor instance."""
        return EventProcessor()

    @pytest.fixture
    def sample_pr_event(self):
        """Load sample pull request event."""
        fixture_path = Path(__file__).parent / "fixtures" / "pull_request_opened.json"
        with open(fixture_path) as f:
            return json.load(f)

    def test_extract_repository_info(self, processor, sample_pr_event):
        """Test repository information extraction."""
        repo_info = processor.extract_repository_info(sample_pr_event)

        assert repo_info["name"] == "test-repo"
        assert repo_info["full_name"] == "test-org/test-repo"
        assert repo_info["owner"] == "test-org"
        assert repo_info["url"] == "https://github.com/test-org/test-repo"
        assert repo_info["default_branch"] == "main"
        assert repo_info["private"] is False

    def test_extract_user_info(self, processor):
        """Test user information extraction."""
        user_data = {
            "login": "developer123",
            "name": "John Developer",
            "html_url": "https://github.com/developer123",
            "type": "User",
        }

        user_info = processor.extract_user_info(user_data)

        assert user_info["login"] == "developer123"
        assert user_info["name"] == "John Developer"
        assert user_info["url"] == "https://github.com/developer123"
        assert user_info["type"] == "User"

    def test_extract_user_info_empty(self, processor):
        """Test user information extraction with empty data."""
        user_info = processor.extract_user_info(None)

        assert user_info["login"] == "unknown"
        assert user_info["name"] == "Unknown User"
        assert user_info["url"] == ""

    def test_format_pull_request_event(self, processor, sample_pr_event):
        """Test pull request event formatting."""
        message = processor.format_pull_request_event(sample_pr_event, "opened")

        assert "Pull Request #42 opened" in message
        assert "test-org/test-repo" in message
        assert "Add new feature for user authentication" in message
        assert "developer123" in message
        assert "OAuth2 authentication" in message
        assert "https://github.com/test-org/test-repo/pull/42" in message

    def test_format_issue_comment_event(self, processor):
        """Test issue comment event formatting."""
        event = {
            "comment": {
                "body": "This looks good! @reviewer please take a look.",
                "html_url": "https://github.com/test-org/test-repo/issues/42#issuecomment-123",
                "user": {"login": "commenter"},
            },
            "issue": {
                "number": 42,
                "title": "Bug: Application crashes on startup",
                "pull_request": None,
            },
            "repository": {
                "full_name": "test-org/test-repo",
                "html_url": "https://github.com/test-org/test-repo",
            },
        }

        message = processor.format_issue_comment_event(event)

        assert "New comment on Issue #42" in message
        assert "Bug: Application crashes on startup" in message
        assert "commenter" in message
        assert "@reviewer please take a look" in message
        assert "This comment contains mentions" in message

    def test_format_pull_request_review_event(self, processor):
        """Test pull request review event formatting."""
        event = {
            "review": {
                "state": "approved",
                "body": "LGTM! Great work on this feature.",
                "html_url": "https://github.com/test-org/test-repo/pull/42#pullrequestreview-123",
                "user": {"login": "reviewer123"},
            },
            "pull_request": {"number": 42, "title": "Add new feature"},
            "repository": {
                "full_name": "test-org/test-repo",
                "html_url": "https://github.com/test-org/test-repo",
            },
        }

        message = processor.format_pull_request_review_event(event)

        assert "reviewer123 approved PR #42" in message
        assert "Add new feature" in message
        assert "APPROVED" in message
        assert "LGTM! Great work" in message

    def test_format_push_event(self, processor):
        """Test push event formatting."""
        event = {
            "ref": "refs/heads/main",
            "before": "abc123def456789",
            "after": "xyz789abc123456",
            "pusher": {"name": "developer123"},
            "commits": [
                {
                    "id": "commit1234567890",
                    "message": "Fix: Resolve memory leak in data processor\n\nDetailed description",
                    "author": {"name": "developer123"},
                },
                {
                    "id": "commit0987654321",
                    "message": "Update dependencies",
                    "author": {"name": "developer123"},
                },
            ],
            "repository": {
                "full_name": "test-org/test-repo",
                "html_url": "https://github.com/test-org/test-repo",
            },
        }

        message = processor.format_push_event(event)

        assert "Push to main branch" in message
        assert "developer123" in message
        assert "2 new commit(s)" in message
        assert "Fix: Resolve memory leak" in message
        assert "Update dependencies" in message

    def test_format_issues_event(self, processor):
        """Test issues event formatting."""
        event = {
            "action": "opened",
            "issue": {
                "number": 123,
                "title": "Feature Request: Add dark mode",
                "body": "It would be great to have a dark mode option.",
                "html_url": "https://github.com/test-org/test-repo/issues/123",
                "user": {"login": "user123"},
                "labels": [{"name": "enhancement"}, {"name": "ui"}],
            },
            "repository": {
                "full_name": "test-org/test-repo",
                "html_url": "https://github.com/test-org/test-repo",
            },
        }

        message = processor.format_issues_event(event, "opened")

        assert "Issue #123 opened" in message
        assert "Feature Request: Add dark mode" in message
        assert "user123" in message
        assert "enhancement, ui" in message
        assert "dark mode option" in message

    def test_process_event_pull_request(self, processor, sample_pr_event):
        """Test processing pull request event."""
        state = processor.process_event("pull_request", sample_pr_event)

        assert isinstance(state, State)
        assert len(state.messages) == 2
        assert isinstance(state.messages[0], SystemMessage)
        assert isinstance(state.messages[1], HumanMessage)

        # Check system message
        system_content = state.messages[0].content
        assert "pull_request" in system_content
        assert "test-org/test-repo" in system_content

        # Check human message
        human_content = state.messages[1].content
        assert "Pull Request #42 opened" in human_content

        # Check project
        assert state.project is not None
        assert state.project.name == "test-repo"

    def test_process_event_unsupported(self, processor):
        """Test processing unsupported event type."""
        event = {
            "action": "created",
            "repository": {
                "name": "test-repo",
                "full_name": "test-org/test-repo",
                "html_url": "https://github.com/test-org/test-repo",
            },
        }

        state = processor.process_event("unknown_event", event)

        assert isinstance(state, State)
        assert len(state.messages) == 2
        human_content = state.messages[1].content
        assert "GitHub Event: unknown_event" in human_content
        assert "Raw Event Data:" in human_content

    def test_should_process_event_skip_actions(self, processor):
        """Test skipping certain actions."""
        # Should skip labeled action for pull_request
        event = {"action": "labeled", "sender": {"type": "User", "login": "user123"}}
        assert processor.should_process_event("pull_request", event) is False

        # Should process opened action
        event = {"action": "opened", "sender": {"type": "User", "login": "user123"}}
        assert processor.should_process_event("pull_request", event) is True

    def test_should_process_event_skip_bot(self, processor):
        """Test skipping bot events."""
        event = {
            "action": "opened",
            "sender": {"type": "Bot", "login": "dependabot[bot]"},
        }
        assert processor.should_process_event("pull_request", event) is False

        # Should process human events
        event = {"action": "opened", "sender": {"type": "User", "login": "human-user"}}
        assert processor.should_process_event("pull_request", event) is True

    def test_should_process_event_assigned_action(self, processor):
        """Test processing assigned actions."""
        # Should process assigned action for issues
        event = {"action": "assigned", "sender": {"type": "User", "login": "user123"}}
        assert processor.should_process_event("issues", event) is True

        # Should process assigned action for pull requests
        assert processor.should_process_event("pull_request", event) is True

        # Should still skip unassigned action
        event = {"action": "unassigned", "sender": {"type": "User", "login": "user123"}}
        assert processor.should_process_event("issues", event) is False
        assert processor.should_process_event("pull_request", event) is False

    def test_create_system_context(self, processor):
        """Test system context creation."""
        repo_info = {
            "full_name": "test-org/test-repo",
            "url": "https://github.com/test-org/test-repo",
            "private": True,
        }

        context = processor.create_system_context("pull_request", repo_info)

        assert "processing a GitHub webhook event" in context
        assert "pull_request" in context
        assert "test-org/test-repo" in context
        assert "Private Repository: True" in context


class TestGlobalInstances:
    """Test global instance management."""

    def test_get_event_processor_singleton(self):
        """Test EventProcessor singleton pattern."""
        processor1 = get_event_processor()
        processor2 = get_event_processor()

        assert processor1 is processor2
