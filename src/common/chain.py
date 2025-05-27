"""Define helpers for chains."""

import functools
from typing import Any, Callable, Coroutine

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig


def skip_on_summary_and_tool_errors(
    *,
    error_message="I encountered a fatal error.\n{error}",
    summary_message="I have summarized my result\n{summary}.",
):
    """Return a handler that exits on a tool error or when a summary has been created."""

    async def _exit_on_summary_or_error(state: Any, config: RunnableConfig, **kwargs):
        messages: list[BaseMessage] = state.messages
        if messages and messages[-1].type == "tool":
            tool_message: ToolMessage = messages[-1]
            if tool_message.status == "error":
                return {
                    "messages": [
                        AIMessage(
                            content=error_message.format(error=tool_message.content)
                        )
                    ],
                    "error": tool_message.content,
                }

            if state.summary:
                return {
                    "messages": [
                        AIMessage(content=summary_message.format(summary=state.summary))
                    ]
                }
        return None

    return _exit_on_summary_or_error


def prechain(handler: Callable[..., Coroutine[Any, Any, Any]]):
    """Invoke the handler before a runnable is invoked. If the handler returns a result the runnable is skipped."""

    def _create_prechain(func):
        @functools.wraps(func)
        async def _wrapper(
            *args,
            **kwargs,
        ) -> dict:
            if result := await handler(*args, **kwargs):
                return result
            return await func(*args, **kwargs)

        return _wrapper

    return _create_prechain
