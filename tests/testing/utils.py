from langchain_core.messages import AIMessage, AnyMessage, ToolMessage


def get_tool_messages_count(messages: list[AnyMessage]) -> dict[str, int]:
    tool_count = {}
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_count[message.name] = tool_count.get(message.name, 0) + 1
    return tool_count


def get_tool_args_with_names(messages: list[AnyMessage], tool_name: str) -> list[dict]:
    tool_args_list = []

    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call["name"] == tool_name:
                    args_dict = tool_call.get("args", {})
                    tool_args_list.append(args_dict)

    return tool_args_list
