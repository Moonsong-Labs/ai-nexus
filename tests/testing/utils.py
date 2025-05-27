from langchain_core.messages import AnyMessage, ToolMessage


def get_tool_messages_count(messages: list[AnyMessage]) -> dict[str, int]:
    tool_count = {}
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_count[message.name] = tool_count.get(message.name, 0) + 1
    return tool_count
