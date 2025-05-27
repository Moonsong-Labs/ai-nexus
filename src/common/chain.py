"""Define helpers for chains."""

import functools
from collections import defaultdict
from typing import Any, Callable, Coroutine

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig


def skip_on_summary_and_tool_errors(
    *,
    error_threshold: int = 3,
    error_message: str = "I encountered a fatal error.\n{error}",
    summary_message: str = "I have summarized my result\n{summary}.",
):
    r"""Return a handler function that halts execution based on specific conditions.

    The handler will exit if a tool encounters an error a certain number
    of consecutive times, or if a summary message is generated. This is
    useful for preventing infinite loops or runaway processes in automated
    workflows.

    Args:
        error_threshold: The maximum number of consecutive tool errors allowed before exiting. Defaults to 3.
            A value of 1 or lower means every error will lead to a skip.
        error_message: The message to return when the maximum number of consecutive errors is reached.
            The string should include "{error}" which will be replaced with the error
            message from the tool. Defaults to "I encountered a fatal error.\n{error}".
        summary_message: The message to return when  a summary has been created.
            The string should include "{summary}" which will be replaced with the summary.
            Defaults to "I have summarized my result\n{summary}.".

    Returns:
        A handler function that can be used to check for tool errors or
        summary messages and exit accordingly.
    """
    current_consecutive_errors: dict[str, int] = defaultdict(int)

    async def _exit_on_summary_or_error(state: Any, config: RunnableConfig, **kwargs):
        messages: list[BaseMessage] = state.messages
        if messages and messages[-1].type == "tool":
            tool_message: ToolMessage = messages[-1]
            # reset if tool success
            if tool_message.status == "success":
                current_consecutive_errors[tool_message.name] = 0
            elif tool_message.status == "error":
                current_consecutive_errors[tool_message.name] += 1

                # do nothing if number of errors is low
                if current_consecutive_errors[tool_message.name] < error_threshold:
                    return None

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
