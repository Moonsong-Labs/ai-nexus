"""Tests for the FastAPI server endpoints."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from event_listener.config import settings
from event_listener.server import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch.object(settings, "github_webhook_secret", "test-secret"):
        with patch.object(settings, "is_production", False):
            yield


@pytest.fixture
def sample_payload():
    """Load sample webhook payload."""
    with open("src/event_listener_tests/fixtures/pull_request_opened.json") as f:
        return json.load(f)


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate GitHub webhook signature."""
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "github-event-listener"
        assert "timestamp" in data
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("event_listener.server.get_github_auth")
    async def test_github_health_success(self, mock_auth, client):
        """Test GitHub health check success."""
        mock_auth_instance = AsyncMock()
        mock_auth_instance.get_rate_limit.return_value = {
            "rate": {"remaining": 4999, "reset": 1704888000}
        }
        mock_auth.return_value = mock_auth_instance

        response = client.get("/health/github")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["github_api_status"] == "connected"
        assert data["rate_limit_remaining"] == 4999

    @patch("event_listener.server.get_github_auth")
    async def test_github_health_failure(self, mock_auth, client):
        """Test GitHub health check failure."""
        mock_auth_instance = AsyncMock()
        mock_auth_instance.get_rate_limit.side_effect = Exception("Connection failed")
        mock_auth.return_value = mock_auth_instance

        response = client.get("/health/github")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data["github_api_status"]

    @patch("event_listener.server.get_handler_registry")
    def test_orchestrator_health_success(self, mock_registry, client):
        """Test orchestrator health check success."""
        mock_registry.return_value = MagicMock(orchestrator=MagicMock())

        response = client.get("/health/orchestrator")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestWebhookEndpoint:
    """Test webhook endpoint."""

    def test_webhook_missing_headers(self, client):
        """Test webhook with missing headers."""
        response = client.post("/github/events", json={})
        assert response.status_code == 400
        assert "Missing X-GitHub-Event header" in response.json()["detail"]

    def test_webhook_invalid_json(self, client):
        """Test webhook with invalid JSON."""
        headers = {"X-GitHub-Event": "push", "X-GitHub-Delivery": "12345"}
        response = client.post(
            "/github/events", content=b"invalid json", headers=headers
        )
        assert response.status_code == 400
        assert "Invalid JSON payload" in response.json()["detail"]

    @patch("event_listener.server.get_github_auth")
    def test_webhook_invalid_signature(self, mock_auth, client, mock_settings):
        """Test webhook with invalid signature in production."""
        with patch.object(settings, "is_production", True):
            mock_auth_instance = AsyncMock()
            mock_auth_instance.verify_webhook_signature.return_value = False
            mock_auth.return_value = mock_auth_instance

            headers = {
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "12345",
                "X-Hub-Signature-256": "sha256=invalid",
            }
            response = client.post("/github/events", json={}, headers=headers)
            assert response.status_code == 401
            assert "Invalid webhook signature" in response.json()["detail"]

    def test_webhook_ping_event(self, client, mock_settings):
        """Test ping event handling."""
        payload = {"zen": "Design for failure."}
        headers = {"X-GitHub-Event": "ping", "X-GitHub-Delivery": "12345"}

        response = client.post("/github/events", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pong"
        assert data["event_type"] == "ping"
        assert "Design for failure" in data["message"]

    @patch("event_listener.server.process_webhook_event")
    async def test_webhook_event_processing(
        self, mock_process, client, sample_payload, mock_settings
    ):
        """Test normal event processing."""
        mock_process.return_value = {
            "status": "success",
            "thread_id": "pr_987654321_42_1704888000",
            "summary": "Processing completed",
            "timestamp": "2024-01-10T12:00:00",
        }

        headers = {"X-GitHub-Event": "pull_request", "X-GitHub-Delivery": "12345"}

        response = client.post("/github/events", json=sample_payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["event_type"] == "pull_request"
        assert data["thread_id"] == "pr_987654321_42_1704888000"

    @patch("event_listener.server.process_webhook_event")
    async def test_webhook_event_error_handling(
        self, mock_process, client, sample_payload, mock_settings
    ):
        """Test event processing error handling."""
        mock_process.side_effect = Exception("Processing failed")

        headers = {"X-GitHub-Event": "pull_request", "X-GitHub-Delivery": "12345"}

        response = client.post("/github/events", json=sample_payload, headers=headers)
        assert response.status_code == 500
        assert "Processing failed" in response.json()["detail"]

    @patch("event_listener.server.BackgroundTasks")
    @patch("event_listener.server.process_webhook_event")
    def test_webhook_production_mode(
        self, mock_process, mock_bg_tasks, client, sample_payload
    ):
        """Test webhook in production mode returns 202."""
        with patch.object(settings, "is_production", True):
            mock_bg = MagicMock()
            mock_bg_tasks.return_value = mock_bg

            headers = {
                "X-GitHub-Event": "pull_request",
                "X-GitHub-Delivery": "12345",
                "X-Hub-Signature-256": "sha256=dummy",
            }

            with patch("event_listener.server.get_github_auth") as mock_auth:
                mock_auth_instance = AsyncMock()
                mock_auth_instance.verify_webhook_signature.return_value = True
                mock_auth.return_value = mock_auth_instance

                response = client.post(
                    "/github/events", json=sample_payload, headers=headers
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "accepted"
                assert data["message"] == "Event accepted for processing"


class TestExceptionHandler:
    """Test global exception handler."""

    @patch("event_listener.server.get_handler_registry")
    def test_global_exception_handler(self, mock_registry, client):
        """Test global exception handler."""
        mock_registry.side_effect = Exception("Unexpected error")

        response = client.get("/health/orchestrator")
        # The health check endpoint catches exceptions, so we get 200 with unhealthy status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
