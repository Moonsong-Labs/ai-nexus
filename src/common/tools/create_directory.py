"""Common tool for creating directories."""

import os

from langchain_core.tools import tool


@tool("create_directory", parse_docstring=True)
def create_directory(directory_path: str) -> str:
    """Create a directory at the specified path.

    Args:
        directory_path: Path to the directory. Relative from current path.

    Returns:
        A message indicating success or failure
    """
    try:
        # Create parent directories if they don't exist
        os.makedirs(directory_path, exist_ok=False)

        return f"Successfully created directory: {directory_path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"
