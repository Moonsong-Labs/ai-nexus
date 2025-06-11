"""Represents a webapp."""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    """Custom middleware."""
    async def dispatch(self, request: Request, call_next):  # noqa: D102
        response = await call_next(request)
        response.headers["X-Custom-Name"] = "ai-nexus"
        return response


# Add the middleware to the app
app.add_middleware(CustomHeaderMiddleware)


@app.get("/github-hook")
def github_hook():
    """Handle github event webhooks."""
    return {"status": "OK"}
