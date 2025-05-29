from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


def decode_base_message(message: dict[str, Any]) -> BaseMessage:
    """Transforms a message dictionary to a BaseMessage object."""

    role = message["role"]
    content = message["content"]

    if role == "human":
        return HumanMessage(content=content)
    elif role == "ai":
        if tool_calls := message.get("tool_calls"):
            return AIMessage(content=content, tool_calls=tool_calls)
        else:
            return AIMessage(content=content)
    elif role == "system":
        return SystemMessage(content=content)
    elif role == "tool":
        tool_call_id = message["tool_call_id"]
        name = message.get("name", "")
        status = message.get("status", "success")
        return ToolMessage(
            content=content, tool_call_id=tool_call_id, name=name, status=status
        )
    else:
        raise ValueError(f"Unknown role: {role}")


def decode_base_messages(messages: list[dict[str, Any]]) -> list[BaseMessage]:
    """Transforms a list of message dictionaries to a list of BaseMessage objects."""
    return [decode_base_message(message) for message in messages]
