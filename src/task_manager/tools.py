"""Define the agent's tools."""

import os

from langchain.tools import tool


@tool
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


@tool
def create_file(file_path: str, content: str) -> str:
    """Create a file at the specified path.

    Args:
        file_path: Path where the file should be created
        content: Content to write to the file

    Returns:
        A message indicating success or failure
    """
    try:
        # Create parent directories if they don't exist
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write the content to the file
        with open(file_path, "w") as f:
            f.write(content)

        return f"Successfully created file: {file_path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"


@tool
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
