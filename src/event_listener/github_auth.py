"""GitHub App authentication and token management."""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
import jwt

from .config import settings


class TokenCache:
    """Simple in-memory token cache with expiration."""

    def __init__(self):
        self._cache: Dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        """Get token from cache if not expired."""
        async with self._lock:
            if key in self._cache:
                token, expires_at = self._cache[key]
                if time.time() < expires_at:
                    return token
                del self._cache[key]
        return None

    async def set(self, key: str, token: str, expires_in: int):
        """Store token with expiration time."""
        async with self._lock:
            # Subtract 60 seconds to refresh before actual expiration
            expires_at = time.time() + expires_in - 60
            self._cache[key] = (token, expires_at)

    async def clear(self):
        """Clear all cached tokens."""
        async with self._lock:
            self._cache.clear()


class GitHubAuth:
    """Handles GitHub App authentication and token management."""

    def __init__(self):
        self.app_id = settings.github_app_id
        self.installation_id = settings.github_installation_id
        self.private_key = settings.github_app_private_key
        self.api_url = settings.github_api_url
        self._token_cache = TokenCache()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url, headers=settings.github_headers, timeout=30.0
            )
        return self._client

    async def close(self):
        """Close HTTP client and clear cache."""
        await self._token_cache.clear()
        if self._client:
            await self._client.aclose()
            self._client = None

    def generate_jwt(self) -> str:
        """
        Generate JWT token for GitHub App authentication.

        Returns:
            str: JWT token valid for 10 minutes
        """
        now = int(time.time())

        payload = {
            "iat": now,
            "exp": now + 600,  # 10 minutes
            "iss": self.app_id,
            "alg": "RS256",
        }

        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def get_installation_token(
        self, installation_id: Optional[str] = None
    ) -> str:
        """
        Get or refresh installation access token.

        Args:
            installation_id: Optional specific installation ID

        Returns:
            str: Installation access token

        Raises:
            httpx.HTTPStatusError: If token request fails
        """
        installation_id = installation_id or self.installation_id
        cache_key = f"installation_{installation_id}"

        # Check cache first
        cached_token = await self._token_cache.get(cache_key)
        if cached_token:
            return cached_token

        # Generate new token
        jwt_token = self.generate_jwt()

        response = await self.client.post(
            f"/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        response.raise_for_status()

        data = response.json()
        token = data["token"]

        # Cache the token
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        expires_in = int((expires_at - datetime.now(expires_at.tzinfo)).total_seconds())
        await self._token_cache.set(cache_key, token, expires_in)

        return token

    async def get_authenticated_client(
        self, installation_id: Optional[str] = None
    ) -> httpx.AsyncClient:
        """
        Get an authenticated HTTP client for GitHub API requests.

        Args:
            installation_id: Optional specific installation ID

        Returns:
            httpx.AsyncClient: Authenticated client
        """
        token = await self.get_installation_token(installation_id)

        return httpx.AsyncClient(
            base_url=self.api_url,
            headers={**settings.github_headers, "Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    async def get_rate_limit(
        self, installation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Args:
            installation_id: Optional specific installation ID

        Returns:
            dict: Rate limit information
        """
        async with await self.get_authenticated_client(installation_id) as client:
            response = await client.get("/rate_limit")
            response.raise_for_status()
            return response.json()

    @asynccontextmanager
    async def authenticated_request(self, installation_id: Optional[str] = None):
        """
        Context manager for authenticated GitHub API requests.

        Usage:
            async with auth.authenticated_request() as client:
                response = await client.get("/repos/owner/repo")
        """
        client = await self.get_authenticated_client(installation_id)
        try:
            yield client
        finally:
            await client.aclose()


# Global auth instance
_auth_instance: Optional[GitHubAuth] = None


def get_github_auth() -> GitHubAuth:
    """Get or create global GitHub auth instance."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = GitHubAuth()
    return _auth_instance


async def cleanup_auth():
    """Cleanup global auth instance."""
    global _auth_instance
    if _auth_instance:
        await _auth_instance.close()
        _auth_instance = None
