"""Convert GitHub webhook payloads to OrchestratorGraph State objects."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage


class EventProcessor:
    """Converts GitHub events to State objects for orchestrator processing."""

    @staticmethod
    def extract_repository_info(event: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract repository information from event payload.

        Args:
            event: GitHub webhook event payload

        Returns:
            dict: Repository information including name, owner, url
        """
        repository = event.get("repository", {})
        return {
            "name": repository.get("name", ""),
            "full_name": repository.get("full_name", ""),
            "owner": repository.get("owner", {}).get("login", ""),
            "url": repository.get("html_url", ""),
            "default_branch": repository.get("default_branch", "main"),
            "private": repository.get("private", False),
        }

    @staticmethod
    def extract_user_info(user_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract user information from event data."""
        if not user_data:
            return {"login": "unknown", "name": "Unknown User", "url": ""}

        return {
            "login": user_data.get("login", "unknown"),
            "name": user_data.get("name") or user_data.get("login", "Unknown"),
            "url": user_data.get("html_url", ""),
            "type": user_data.get("type", "User"),
        }

    @staticmethod
    def format_assigned_issue_event(event: Dict[str, Any]) -> str:
        """Format issue assignment event into human-readable message."""
        issue = event.get("issue", {})
        repo_info = EventProcessor.extract_repository_info(event)
        user_info = EventProcessor.extract_user_info(issue.get("user"))
        assignee_info = EventProcessor.extract_user_info(issue.get("assignee"))

        issue_number = issue.get("number", "unknown")
        issue_title = issue.get("title", "Untitled")
        issue_body = issue.get("body", "No description provided")
        issue_url = issue.get("html_url", "")
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        message = f"""Issue #{issue_number} assigned to {assignee_info["login"]} in {repo_info["full_name"]}

**Title:** {issue_title}
**Author:** {user_info["login"]}
**Assigned to:** {assignee_info["login"]}
**URL:** {issue_url}
**Labels:** {", ".join(labels) if labels else "None"}

**Description:**
{issue_body}

**Repository:** {repo_info["url"]}
**Action Required:** Please analyze this issue and provide a solution plan."""

        return message

    @staticmethod
    def format_comment_trigger_event(event: Dict[str, Any]) -> str:
        """Format issue comment trigger event into human-readable message."""
        issue = event.get("issue", {})
        comment = event.get("comment", {})
        repo_info = EventProcessor.extract_repository_info(event)
        user_info = EventProcessor.extract_user_info(issue.get("user"))
        commenter_info = EventProcessor.extract_user_info(comment.get("user"))

        issue_number = issue.get("number", "unknown")
        issue_title = issue.get("title", "Untitled")
        issue_body = issue.get("body", "No description provided")
        issue_url = issue.get("html_url", "")
        labels = [label.get("name", "") for label in issue.get("labels", [])]

        comment_body = comment.get("body", "")
        comment_url = comment.get("html_url", "")

        message = f"""AI assistance requested for Issue #{issue_number} in {repo_info["full_name"]}

**Title:** {issue_title}
**Author:** {user_info["login"]}
**Requested by:** {commenter_info["login"]}
**URL:** {issue_url}
**Labels:** {", ".join(labels) if labels else "None"}

**Issue Description:**
{issue_body}

**Request Comment:**
{comment_body}
**Comment URL:** {comment_url}

**Repository:** {repo_info["url"]}
**Action Required:** Please analyze this issue and provide a solution plan."""

        return message

    @staticmethod
    def create_system_context(event_type: str, repo_info: Dict[str, str]) -> str:
        """Create system context message for the orchestrator."""
        return f"""You are processing a GitHub webhook event.

**Event Type:** {event_type}
**Repository:** {repo_info["full_name"]}
**Repository URL:** {repo_info["url"]}
**Private Repository:** {repo_info["private"]}

Please analyze this event and determine the appropriate action to take. You have access to GitHub tools to interact with the repository."""

    def process_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Process a GitHub webhook event and convert to State object.

        Args:
            event_type: GitHub event type (e.g., "pull_request", "issues")
            event_data: Raw webhook payload

        Returns:
            State: Configured state object for orchestrator
        """
        # Lazy imports to avoid loading orchestrator at module level
        from common.state import Project
        from orchestrator.state import State

        repo_info = self.extract_repository_info(event_data)
        action = event_data.get("action", "")

        # Format event-specific message
        if event_type == "issues" and action == "assigned":
            human_message = self.format_assigned_issue_event(event_data)
        elif event_type == "issue_comment" and action == "created":
            human_message = self.format_comment_trigger_event(event_data)
        else:
            # Generic formatting for unsupported events
            human_message = f"""Unsupported GitHub Event: {event_type} ({action}) in {repo_info["full_name"]}

**Event Type:** {event_type}
**Action:** {action}
**Repository:** {repo_info["url"]}

**Note:** This service processes issue assignment and comment trigger events.

Raw Event Data:
{json.dumps(event_data, indent=2)[:500]}..."""

        # Create messages
        system_message = SystemMessage(
            content=self.create_system_context(event_type, repo_info)
        )
        human_msg = HumanMessage(content=human_message)

        # Create project from repository name
        project = None
        if repo_info["name"]:
            project = Project.from_name(repo_info["name"])

        # Create and return State
        return State(messages=[system_message, human_msg], project=project)

    def should_process_event(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Determine if an event should be processed.

        Args:
            event_type: GitHub event type
            event_data: Event payload

        Returns:
            bool: True if event should be processed
        """
        action = event_data.get("action", "")

        # Process issue assignment events to AI bots
        if event_type == "issues" and action == "assigned":
            issue = event_data.get("issue", {})
            assignee = issue.get("assignee", {})
            assignee_login = assignee.get("login", "")

            # Only process if assigned to our AI bot
            if assignee_login.endswith("[bot]") or "ai-nexus" in assignee_login.lower():
                return True
            return False

        # Process comment events with AI bot trigger phrases
        if event_type == "issue_comment" and action == "created":
            comment = event_data.get("comment", {})
            comment_body = comment.get("body", "")

            # Don't process comments from bots (avoid loops)
            commenter = comment.get("user", {})
            if commenter.get("type") == "Bot":
                return False

            # Only activate if the bot is explicitly mentioned by its full name
            # Check for exact mentions (case-insensitive)
            bot_mentions = ["ai-nexus-bot", "@ai-nexus-bot"]

            comment_lower = comment_body.lower()
            for mention in bot_mentions:
                if mention in comment_lower:
                    return True

            return False

        # Skip all other event types and actions
        return False


# Global processor instance
_processor_instance: Optional[EventProcessor] = None


def get_event_processor() -> EventProcessor:
    """Get or create global event processor instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = EventProcessor()
    return _processor_instance
