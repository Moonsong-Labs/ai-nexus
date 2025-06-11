"""FastAPI application for GitHub webhook event listener."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import dotenv
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import settings
from .github_auth import cleanup_auth, get_github_auth
from .handlers import cleanup_handlers, get_handler_registry

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    service: str = "github-event-listener"


class GitHubHealthResponse(HealthResponse):
    """GitHub connectivity health check response."""

    github_api_status: str
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[str] = None


class EventResponse(BaseModel):
    """Webhook event processing response."""

    status: str
    event_type: str
    timestamp: str
    thread_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


# Semaphore for concurrent event processing
event_semaphore = asyncio.Semaphore(settings.max_concurrent_events)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting GitHub Event Listener service")
    logger.info(f"Configured for GitHub App ID: {settings.github_app_id}")
    logger.info(
        f"Listening on {settings.event_listener_host}:{settings.event_listener_port}"
    )

    # Initialize components
    auth = get_github_auth()
    registry = get_handler_registry()

    yield

    # Shutdown
    logger.info("Shutting down GitHub Event Listener service")
    await cleanup_auth()
    await cleanup_handlers()


# Create FastAPI app
app = FastAPI(
    title="GitHub Event Listener",
    description="FastAPI microservice for processing GitHub issue assignment events",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow().isoformat(), version="0.1.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow().isoformat(), version="0.1.0"
    )


@app.get("/health/github", response_model=GitHubHealthResponse)
async def github_health_check():
    """Check GitHub API connectivity."""
    try:
        auth = get_github_auth()
        rate_limit = await auth.get_rate_limit()

        return GitHubHealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version="0.1.0",
            github_api_status="connected",
            rate_limit_remaining=rate_limit.get("rate", {}).get("remaining"),
            rate_limit_reset=datetime.fromtimestamp(
                rate_limit.get("rate", {}).get("reset", 0)
            ).isoformat()
            if rate_limit.get("rate", {}).get("reset")
            else None,
        )
    except Exception as e:
        logger.error(f"GitHub health check failed: {str(e)}")
        return GitHubHealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="0.1.0",
            github_api_status=f"error: {str(e)}",
        )


@app.get("/health/orchestrator", response_model=HealthResponse)
async def orchestrator_health_check():
    """Check orchestrator availability."""
    try:
        registry = get_handler_registry()
        # Check if registry has handlers and can create orchestrator
        if registry and registry._handlers:
            # Try to access the orchestrator from the first handler
            handler = registry._handlers[0]
            orchestrator = handler.orchestrator  # This will lazy load it
            if orchestrator:
                return HealthResponse(
                    status="healthy",
                    timestamp=datetime.utcnow().isoformat(),
                    version="0.1.0",
                )
        raise Exception("Orchestrator not available")
    except Exception as e:
        logger.error(f"Orchestrator health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy", timestamp=datetime.utcnow().isoformat(), version="0.1.0"
        )


async def process_webhook_event(
    event_type: str, event_data: Dict[str, Any], delivery_id: str
) -> Dict[str, Any]:
    """Process webhook event asynchronously.

    Args:
        event_type: GitHub event type
        event_data: Event payload
        delivery_id: GitHub delivery ID

    Returns:
        dict: Processing result
    """
    async with event_semaphore:
        logger.info(f"Processing {event_type} event (delivery: {delivery_id})")

        try:
            registry = get_handler_registry()
            result = await registry.handle_event(event_type, event_data)

            logger.info(
                f"Completed processing {event_type} event "
                f"(delivery: {delivery_id}, status: {result.get('status')})"
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to process {event_type} event "
                f"(delivery: {delivery_id}): {str(e)}"
            )
            raise


@app.post("/github/events", response_model=EventResponse)
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_github_delivery: str = Header(None),
):
    """Receive and process GitHub webhook events.

    Args:
        request: FastAPI request object
        x_github_event: GitHub event type header
        x_github_delivery: GitHub delivery ID header

    Returns:
        EventResponse: Processing response
    """
    # Validate headers
    if not x_github_event:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")

    if not x_github_delivery:
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Delivery header")

    # Get raw payload
    payload = await request.body()

    # Parse JSON payload
    try:
        event_data = json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Log event receipt
    repo_name = event_data.get("repository", {}).get("full_name", "unknown")
    logger.info(
        f"Received {x_github_event} event for {repo_name} "
        f"(delivery: {x_github_delivery})"
    )

    # Handle ping event synchronously
    if x_github_event == "ping":
        zen = event_data.get("zen", "")
        return EventResponse(
            status="pong",
            event_type="ping",
            timestamp=datetime.utcnow().isoformat(),
            message=f"Webhook configured successfully. Zen: {zen}",
        )

    # Process event in background
    try:
        # Process synchronously for easier debugging
        result = await process_webhook_event(
            x_github_event, event_data, x_github_delivery
        )

        return EventResponse(
            status=result.get("status", "unknown"),
            event_type=x_github_event,
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            thread_id=result.get("thread_id"),
            message=result.get("summary"),
            error=result.get("error"),
        )

    except Exception as e:
        logger.error(f"Failed to process event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler.

    Args:
        request: FastAPI request
        exc: Exception that occurred

    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if settings.is_production else str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        app,
        host=settings.event_listener_host,
        port=settings.event_listener_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run_server()
