"""Common tool for creating files."""

import os

from langchain_core.tools import tool


@tool("create_file", parse_docstring=True)
def create_file(file_path: str, content: str) -> str:
    """Create a file at the specified path.

    Args:
        file_path: Path where the file should be created
        content: Content to write to the file

    Returns:
        A message indicating success or failure
    """
    try:
        # Check if directory exist
        directory = os.path.dirname(file_path)
        if os.path.isdir(directory):
            # Write the content to the file
            with open(file_path, "w") as f:
                f.write(content)

            return f"Successfully created file: {file_path}"
        return f"Error: Directory '{directory}' does not exist."
    except Exception as e:
        return f"Error creating file: {str(e)}"
