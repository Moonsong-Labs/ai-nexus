"""Contains wrappers fot github tools."""

from typing import Annotated, List

from langchain_core.tools import BaseTool, tool


def wrap_update_file(update_file_tool: BaseTool) -> BaseTool:
    @tool
    def update_file(
        file_path: Annotated[str, "the file path to update the contents of"],
        old_contents: Annotated[str, "the string to replace"],
        new_contents: Annotated[str, "the string to insert in place of `old_contents`"],
    ) -> str:
        """Update the given file."""
        formatted = f"{file_path}\n\nOLD <<<<\n{old_contents}\n>>>> OLD\nNEW <<<<\n{new_contents}\n>>>> NEW"
        return update_file_tool.invoke({"formatted_file_update": formatted})

    return update_file


def wrap_github_tools(tools: List[BaseTool]) -> List[BaseTool]:
    """Wrap the given github tools into easier interfaces for the agents to use."""
    wrappers = {"update_file": wrap_update_file}
    return [
        wrappers[orig.name](orig) if (orig.name in wrappers) else orig for orig in tools
    ]

__all__ = [wrap_github_tools.__name__]
