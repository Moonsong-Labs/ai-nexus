import math

from langchain_core.messages import AIMessage, AnyMessage


def get_tool_args_with_names(messages: list[AnyMessage], tool_name: str) -> list[dict]:        
    tool_args_list = [
        tool_call["args"]
        for message in messages
        if isinstance(message, AIMessage) and message.tool_calls
        for tool_call in message.tool_calls
        if tool_call["name"] == tool_name
    ]

    return tool_args_list

def get_list_diff(list1, list2):
    """
    Finds the elements that are missing from list1 and extra in list2,
    considering duplicate elements and preserving order.

    Args:
        list1: The first list.
        list2: The second list.

    Returns:
        A tuple containing two lists:
        - missing: Elements that are in list1 but not in list2, in order.
        - extra: Elements that are in list2 but not in list1, in order.
    """

    missing = []
    extra = []
    list2_copy = list2[:]  # Create a copy to avoid modifying the original list

    for element in list1:
        if element in list2_copy:
            list2_copy.remove(element)
        else:
            missing.append(element)

    extra = list2_copy

    return missing, extra


def round_half_up(n):
    """Rounds a number up if its decimal part is 0.5 or greater."""
    if n % 1 == 0:  # Check if n is an integer return n
        return n
    return math.ceil(n + 1e-10)


def round_to(number, decimal_places=2):
    """Rounds a number to the specified number of decimal places, rounding half up."""
    scale = 10**decimal_places
    return round_half_up(number * scale) / scale
