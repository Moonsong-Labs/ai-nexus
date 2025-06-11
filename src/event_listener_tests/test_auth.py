"""Tests for GitHub authentication module."""

import asyncio
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import jwt
import pytest

from event_listener.github_auth import GitHubAuth, TokenCache, get_github_auth


class TestTokenCache:
    """Test token cache functionality."""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting tokens from cache."""
        cache = TokenCache()

        # Set token
        await cache.set("test_key", "test_token", expires_in=3600)

        # Get token
        token = await cache.get("test_key")
        assert token == "test_token"

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test token expiration."""
        cache = TokenCache()

        # Set token with 1 second expiration
        await cache.set("test_key", "test_token", expires_in=61)  # 61 - 60 = 1 second

        # Token should be available immediately
        token = await cache.get("test_key")
        assert token == "test_token"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Token should be expired
        token = await cache.get("test_key")
        assert token is None

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test clearing cache."""
        cache = TokenCache()

        # Set multiple tokens
        await cache.set("key1", "token1", expires_in=3600)
        await cache.set("key2", "token2", expires_in=3600)

        # Clear cache
        await cache.clear()

        # Tokens should be gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


class TestGitHubAuth:
    """Test GitHub authentication."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("event_listener.github_auth.settings") as mock:
            mock.github_app_id = "123456"
            mock.github_installation_id = "12345678"
            mock.github_app_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAtest
-----END RSA PRIVATE KEY-----"""
            mock.github_webhook_secret = "test-secret"
            mock.github_api_url = "https://api.github.com"
            mock.github_headers = {"Accept": "application/vnd.github+json"}
            yield mock

    def test_jwt_generation(self, mock_settings):
        """Test JWT token generation."""
        auth = GitHubAuth()

        with patch("time.time", return_value=1234567890):
            token = auth.generate_jwt()

        # Decode without verification (we don't have the public key)
        decoded = jwt.decode(token, options={"verify_signature": False})

        assert decoded["iss"] == "123456"
        assert decoded["iat"] == 1234567890
        assert decoded["exp"] == 1234567890 + 600  # 10 minutes

    @pytest.mark.asyncio
    async def test_get_installation_token_success(self, mock_settings):
        """Test successful installation token retrieval."""
        auth = GitHubAuth()

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "token": "ghs_test_token_12345",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z",
        }

        with patch.object(auth, "client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_response)

            token = await auth.get_installation_token()

            assert token == "ghs_test_token_12345"

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "/app/installations/12345678/access_tokens" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_installation_token_cached(self, mock_settings):
        """Test installation token caching."""
        auth = GitHubAuth()

        # Set up cached token
        await auth._token_cache.set(
            "installation_12345678", "cached_token", expires_in=3600
        )

        # Should return cached token without API call
        with patch.object(auth, "client") as mock_client:
            token = await auth.get_installation_token()

            assert token == "cached_token"
            mock_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_valid(self, mock_settings):
        """Test valid webhook signature verification."""
        auth = GitHubAuth()

        payload = b'{"test": "data"}'
        signature = (
            "sha256=" + hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()
        )

        is_valid = await auth.verify_webhook_signature(payload, signature)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_invalid(self, mock_settings):
        """Test invalid webhook signature verification."""
        auth = GitHubAuth()

        payload = b'{"test": "data"}'
        signature = "sha256=invalid_signature"

        is_valid = await auth.verify_webhook_signature(payload, signature)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_webhook_signature_wrong_format(self, mock_settings):
        """Test webhook signature with wrong format."""
        auth = GitHubAuth()

        payload = b'{"test": "data"}'
        signature = "invalid_format"

        is_valid = await auth.verify_webhook_signature(payload, signature)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_get_authenticated_client(self, mock_settings):
        """Test getting authenticated HTTP client."""
        auth = GitHubAuth()

        # Mock get_installation_token
        with patch.object(auth, "get_installation_token") as mock_get_token:
            mock_get_token.return_value = "test_token"

            async with await auth.get_authenticated_client() as client:
                assert isinstance(client, httpx.AsyncClient)
                assert client.headers["Authorization"] == "Bearer test_token"
                assert client.base_url == "https://api.github.com"

    @pytest.mark.asyncio
    async def test_authenticated_request_context_manager(self, mock_settings):
        """Test authenticated request context manager."""
        auth = GitHubAuth()

        with patch.object(auth, "get_installation_token") as mock_get_token:
            mock_get_token.return_value = "test_token"

            async with auth.authenticated_request() as client:
                assert isinstance(client, httpx.AsyncClient)
                assert client.headers["Authorization"] == "Bearer test_token"

    @pytest.mark.asyncio
    async def test_cleanup(self, mock_settings):
        """Test cleanup functionality."""
        auth = GitHubAuth()

        # Create a client
        _ = auth.client
        assert auth._client is not None

        # Add token to cache
        await auth._token_cache.set("test", "token", expires_in=3600)

        # Cleanup
        await auth.close()

        # Verify cleanup
        assert auth._client is None
        assert await auth._token_cache.get("test") is None


class TestGlobalInstances:
    """Test global instance management."""

    def test_get_github_auth_singleton(self):
        """Test GitHubAuth singleton pattern."""
        auth1 = get_github_auth()
        auth2 = get_github_auth()

        assert auth1 is auth2

    @pytest.mark.asyncio
    async def test_cleanup_auth(self):
        """Test auth cleanup."""
        from event_listener.github_auth import _auth_instance, cleanup_auth

        # Create instance
        auth = get_github_auth()
        assert _auth_instance is not None

        # Cleanup
        await cleanup_auth()

        # Import again to check
        from event_listener.github_auth import _auth_instance

        assert _auth_instance is None
