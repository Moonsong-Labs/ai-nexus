"""Represents a webapp."""

# ruff: noqa: T201

from typing import Any, Optional

from fastapi import FastAPI, Request
from langgraph_sdk import get_client
from langgraph_sdk.schema import Run
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


@app.post("/github-hook")
async def github_hook(request: Request):
    """Handle github event webhooks."""
    github_event = request.headers.get("x-github-event")
    payload = await request.json()
    print("=== RAW PAYLOAD ===")
    print(payload)
    print("=== RAW PAYLOAD::END ===")
    print()

    print(
        f"Received Event from @{payload['sender']['login']} on {payload['repository']['full_name']}:  {github_event} ({payload['action']})\n{payload['issue']['body']}\n"
    )

    try:
        if payload["action"] in ["opened", "edited"]:
            run = await orchestrate(
                "I want to build a personal website",  # use payload["issue"]["body"]
                metadata={
                    "trigger": "github_event",
                    "event": github_event,
                    "event_action": payload["action"],
                    "repository": payload["repository"]["full_name"],
                    "sender": payload["sender"]["login"],
                },
            )

            print(run)
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

    return {
        "status": "OK",
        "assisstant_id": run["assistant_id"],
        "run_id": run["run_id"],
        "run_status": run["status"],
    }


API_URL = "http://127.0.0.1:8000"
orchestrator_id = None


async def orchestrate(content, *, metadata: Optional[dict[str, Any]] = None) -> Run:
    """Dispatch a run to the orchestrator."""
    global orchestrator_id

    client = get_client(url=API_URL)

    if not orchestrator_id:
        print("looking up orchestrator id...")
        assistants = await client.assistants.search(
            graph_id="orchestrator",
            limit=1,
        )
        print(assistants)
        if not assistants:
            print("orchestrator not found")
            raise Exception("orchestrator not found")

        orchestrator_id = assistants[0]["assistant_id"]

    print("found orchestrator {orchestrator_id}")

    # TODO: Create an orchestrator that handles issue-to-PR and modify the input
    thread = await client.threads.create()
    run = await client.runs.create(
        assistant_id=orchestrator_id,
        thread_id=thread["thread_id"],
        input={"messages": [{"role": "user", "content": content}]},
        metadata=metadata,
    )

    return run
