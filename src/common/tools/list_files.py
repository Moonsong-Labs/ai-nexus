"""Common tool for listing files in directories."""

import os

from langchain_core.tools import tool


@tool("list_files", parse_docstring=True)
def list_files(directory_path: str = ".") -> str:
    """List all files and directories in the specified path.

    Args:
        directory_path: Path to list files from. Defaults to current directory.

    Returns:
        A formatted string listing all files and directories, or an error message.
    """
    try:
        # Check if directory exists
        if not os.path.exists(directory_path):
            return f"Error: Directory '{directory_path}' does not exist."

        if not os.path.isdir(directory_path):
            return f"Error: '{directory_path}' is not a directory."

        # Get list of all files and directories
        items = os.listdir(directory_path)

        # Group by type (directory or file)
        directories = []
        files = []

        for item in items:
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                directories.append(f"📁 {item}/")
            else:
                # Get file size
                size = os.path.getsize(item_path)
                size_str = f"{size} bytes"
                if size > 1024:
                    size_str = f"{size / 1024:.1f} KB"
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.1f} MB"

                files.append(f"📄 {item} ({size_str})")

        # Format the response
        result = f"Contents of '{directory_path}':\n\n"

        if directories:
            result += "Directories:\n"
            result += "\n".join(sorted(directories))
            result += "\n\n"

        if files:
            result += "Files:\n"
            result += "\n".join(sorted(files))

        if not directories and not files:
            result += "Directory is empty."

        return result
    except Exception as e:
        return f"Error listing files: {str(e)}"
