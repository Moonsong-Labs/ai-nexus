"""Tests for event handlers module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from event_listener.handlers import (
    BaseEventHandler,
    HandlerRegistry,
    IssueCommentHandler,
    IssuesHandler,
    PullRequestHandler,
    PullRequestReviewHandler,
    PushHandler,
    get_handler_registry,
    get_orchestrator,
)
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State


class TestBaseEventHandler:
    """Test base event handler functionality."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        mock = MagicMock(spec=OrchestratorGraph)
        mock.compiled_graph = MagicMock()
        mock.compiled_graph.ainvoke = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_invoke_orchestrator_success(self, mock_orchestrator):
        """Test successful orchestrator invocation."""
        # Create a concrete handler for testing
        handler = PullRequestHandler(mock_orchestrator)

        # Mock orchestrator response
        mock_orchestrator.compiled_graph.ainvoke.return_value = {
            "summary": "Processing completed successfully",
            "error": "",
            "messages": [],
        }

        # Create test state
        state = State(messages=[])

        # Invoke orchestrator
        result = await handler.invoke_orchestrator(state, "test_thread_123")

        assert result["status"] == "success"
        assert result["thread_id"] == "test_thread_123"
        assert result["summary"] == "Processing completed successfully"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_invoke_orchestrator_timeout(self, mock_orchestrator):
        """Test orchestrator timeout handling."""
        handler = PullRequestHandler(mock_orchestrator)

        # Mock timeout
        async def slow_invoke(*args, **kwargs):
            await asyncio.sleep(10)

        mock_orchestrator.compiled_graph.ainvoke = slow_invoke

        state = State(messages=[])

        with patch("event_listener.handlers.settings.orchestrator_timeout", 0.1):
            result = await handler.invoke_orchestrator(state, "test_thread_123")

        assert result["status"] == "timeout"
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    async def test_invoke_orchestrator_error(self, mock_orchestrator):
        """Test orchestrator error handling."""
        handler = PullRequestHandler(mock_orchestrator)

        # Mock error
        mock_orchestrator.compiled_graph.ainvoke.side_effect = Exception("Test error")

        state = State(messages=[])
        result = await handler.invoke_orchestrator(state, "test_thread_123")

        assert result["status"] == "error"
        assert result["error"] == "Test error"

    def test_generate_thread_id_pull_request(self, mock_orchestrator):
        """Test thread ID generation for pull request."""
        handler = PullRequestHandler(mock_orchestrator)

        event = {"repository": {"id": 12345}, "pull_request": {"number": 42}}

        with patch("event_listener.handlers.datetime") as mock_dt:
            mock_dt.utcnow.return_value.timestamp.return_value = 1234567890
            thread_id = handler.generate_thread_id(event)

        assert thread_id == "pr_12345_42_1234567890"

    def test_generate_thread_id_issue(self, mock_orchestrator):
        """Test thread ID generation for issue."""
        handler = IssueCommentHandler(mock_orchestrator)

        event = {"repository": {"id": 12345}, "issue": {"number": 99}}

        with patch("event_listener.handlers.datetime") as mock_dt:
            mock_dt.utcnow.return_value.timestamp.return_value = 1234567890
            thread_id = handler.generate_thread_id(event)

        assert thread_id == "issue_12345_99_1234567890"


class TestPullRequestHandler:
    """Test pull request handler."""

    @pytest.fixture
    def handler(self, mock_orchestrator):
        """Create pull request handler."""
        return PullRequestHandler(mock_orchestrator)

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        mock = MagicMock(spec=OrchestratorGraph)
        mock.compiled_graph = MagicMock()
        mock.compiled_graph.ainvoke = AsyncMock(
            return_value={"summary": "Processed", "error": ""}
        )
        return mock

    @pytest.mark.asyncio
    async def test_can_handle_valid(self, handler):
        """Test can_handle with valid pull request event."""
        event = {"X-GitHub-Event": "pull_request", "action": "opened"}
        assert await handler.can_handle(event) is True

    @pytest.mark.asyncio
    async def test_can_handle_invalid_event_type(self, handler):
        """Test can_handle with invalid event type."""
        event = {"X-GitHub-Event": "push", "action": "opened"}
        assert await handler.can_handle(event) is False

    @pytest.mark.asyncio
    async def test_can_handle_invalid_action(self, handler):
        """Test can_handle with invalid action."""
        event = {
            "X-GitHub-Event": "pull_request",
            "action": "labeled",  # Not in handled actions
        }
        assert await handler.can_handle(event) is False

    @pytest.mark.asyncio
    async def test_handle_success(self, handler):
        """Test successful event handling."""
        event = {
            "X-GitHub-Event": "pull_request",
            "action": "opened",
            "pull_request": {"number": 42},
            "repository": {"id": 12345, "full_name": "test/repo"},
        }

        with patch.object(
            handler.event_processor, "should_process_event", return_value=True
        ):
            with patch.object(handler.event_processor, "process_event") as mock_process:
                mock_state = State(messages=[])
                mock_process.return_value = mock_state

                result = await handler.handle(event)

                assert result["status"] == "success"
                mock_process.assert_called_once_with("pull_request", event)

    @pytest.mark.asyncio
    async def test_handle_skip(self, handler):
        """Test skipping event processing."""
        event = {
            "X-GitHub-Event": "pull_request",
            "action": "labeled",
            "pull_request": {"number": 42},
            "repository": {"id": 12345},
        }

        with patch.object(
            handler.event_processor, "should_process_event", return_value=False
        ):
            result = await handler.handle(event)

            assert result["status"] == "skipped"
            assert "not configured for processing" in result["reason"]


class TestIssueCommentHandler:
    """Test issue comment handler."""

    @pytest.fixture
    def handler(self, mock_orchestrator):
        """Create issue comment handler."""
        return IssueCommentHandler(mock_orchestrator)

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        mock = MagicMock(spec=OrchestratorGraph)
        mock.compiled_graph = MagicMock()
        mock.compiled_graph.ainvoke = AsyncMock(
            return_value={"summary": "Processed", "error": ""}
        )
        return mock

    @pytest.mark.asyncio
    async def test_can_handle(self, handler):
        """Test can_handle for issue comment."""
        event = {"X-GitHub-Event": "issue_comment"}
        assert await handler.can_handle(event) is True

        event = {"X-GitHub-Event": "pull_request"}
        assert await handler.can_handle(event) is False


class TestPushHandler:
    """Test push handler."""

    @pytest.fixture
    def handler(self, mock_orchestrator):
        """Create push handler."""
        return PushHandler(mock_orchestrator)

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        mock = MagicMock(spec=OrchestratorGraph)
        mock.compiled_graph = MagicMock()
        mock.compiled_graph.ainvoke = AsyncMock(
            return_value={"summary": "Processed", "error": ""}
        )
        return mock

    @pytest.mark.asyncio
    async def test_can_handle_main_branch(self, handler):
        """Test can_handle for push to main branch."""
        event = {"X-GitHub-Event": "push", "ref": "refs/heads/main"}
        assert await handler.can_handle(event) is True

    @pytest.mark.asyncio
    async def test_can_handle_feature_branch(self, handler):
        """Test can_handle for push to feature branch."""
        event = {"X-GitHub-Event": "push", "ref": "refs/heads/feature/new-feature"}
        assert await handler.can_handle(event) is False


class TestHandlerRegistry:
    """Test handler registry."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        return MagicMock(spec=OrchestratorGraph)

    @pytest.fixture
    def registry(self, mock_orchestrator):
        """Create handler registry."""
        return HandlerRegistry(mock_orchestrator)

    def test_initialization(self, registry):
        """Test registry initialization."""
        assert len(registry._handlers) > 0

        # Check that default handlers are registered
        handler_types = [type(h) for h in registry._handlers]
        assert PullRequestHandler in handler_types
        assert IssueCommentHandler in handler_types
        assert PullRequestReviewHandler in handler_types
        assert PushHandler in handler_types
        assert IssuesHandler in handler_types

    def test_register_custom_handler(self, registry, mock_orchestrator):
        """Test registering custom handler."""

        class CustomHandler(BaseEventHandler):
            async def can_handle(self, event):
                return event.get("X-GitHub-Event") == "custom"

            async def handle(self, event):
                return {"status": "custom"}

        initial_count = len(registry._handlers)
        registry.register(CustomHandler)

        assert len(registry._handlers) == initial_count + 1
        assert isinstance(registry._handlers[-1], CustomHandler)

    @pytest.mark.asyncio
    async def test_handle_event_success(self, registry):
        """Test successful event routing."""
        event_data = {
            "action": "opened",
            "pull_request": {"number": 42},
            "repository": {"id": 12345, "full_name": "test/repo"},
        }

        # Mock the first handler to handle the event
        mock_handler = registry._handlers[0]
        mock_handler.can_handle = AsyncMock(return_value=True)
        mock_handler.handle = AsyncMock(return_value={"status": "handled"})

        result = await registry.handle_event("pull_request", event_data)

        assert result["status"] == "handled"
        assert event_data["X-GitHub-Event"] == "pull_request"

    @pytest.mark.asyncio
    async def test_handle_event_no_handler(self, registry):
        """Test event with no matching handler."""
        event_data = {}

        # Mock all handlers to not handle the event
        for handler in registry._handlers:
            handler.can_handle = AsyncMock(return_value=False)

        result = await registry.handle_event("unknown_event", event_data)

        assert result["status"] == "unhandled"
        assert "No handler registered" in result["reason"]


class TestGlobalInstances:
    """Test global instance management."""

    def test_get_orchestrator_singleton(self):
        """Test orchestrator singleton pattern."""
        with patch("event_listener.handlers.Configuration"):
            orch1 = get_orchestrator()
            orch2 = get_orchestrator()

            assert orch1 is orch2

    def test_get_handler_registry_singleton(self):
        """Test handler registry singleton pattern."""
        with patch("event_listener.handlers.Configuration"):
            reg1 = get_handler_registry()
            reg2 = get_handler_registry()

            assert reg1 is reg2

    @pytest.mark.asyncio
    async def test_cleanup_handlers(self):
        """Test handler cleanup."""
        from event_listener.handlers import (
            _handler_registry,
            _orchestrator_instance,
            cleanup_handlers,
        )

        with patch("event_listener.handlers.Configuration"):
            # Create instances
            get_orchestrator()
            get_handler_registry()

            # Cleanup
            await cleanup_handlers()

            # Import again to check
            from event_listener.handlers import (
                _handler_registry,
                _orchestrator_instance,
            )

            assert _orchestrator_instance is None
            assert _handler_registry is None
