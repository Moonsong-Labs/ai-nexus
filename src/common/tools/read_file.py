"""Common tool for reading files."""

import os

from langchain_core.tools import tool


@tool("read_file", parse_docstring=True)
def read_file(file_path: str) -> str:
    """Read the content of a file and return it as a string.

    Args:
        file_path: Path to the file to read

    Returns:
        The content of the file as a string, or an error message.
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            return f"Error: File does not exist: {file_path}"

        # Check if it's a file (not a directory)
        if not os.path.isfile(file_path):
            return f"Error: Not a file: {file_path}"

        # Read the file
        with open(file_path) as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
