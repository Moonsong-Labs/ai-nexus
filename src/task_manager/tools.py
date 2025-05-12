"""Define the agent's tools."""

import os

from langchain.tools import tool


# Helper function to get and validate the volume directory path
def get_volume_path(requested_path: str = "") -> tuple[bool, str, str]:
    """Get the absolute path to the volume directory and validate a requested path.

    Args:
        requested_path: The path requested by the user

    Returns:
        Tuple of (is_valid, absolute_path, error_message)
        - is_valid: Whether the requested path is valid (within volume dir)
        - absolute_path: The absolute path to use (if valid)
        - error_message: Error message if path is invalid
    """
    # Get the absolute path to the volume directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    task_manager_dir = os.path.join(base_dir, "task_manager")
    volume_dir = os.path.join(task_manager_dir, "volume")

    # Create the volume directory if it doesn't exist
    os.makedirs(volume_dir, exist_ok=True)

    # If no path is provided, use the volume directory
    if not requested_path:
        return True, volume_dir, ""

    # Check if the path is an absolute path
    if os.path.isabs(requested_path):
        abs_path = requested_path
    else:
        # If it's relative, make it relative to the volume directory
        abs_path = os.path.join(volume_dir, requested_path)

    # Normalize the path to resolve any parent directory references (..)
    normalized_path = os.path.normpath(abs_path)

    # Check if the normalized path is within the volume directory
    if not normalized_path.startswith(volume_dir):
        return (
            False,
            "",
            f"Error: Access denied. Path must be within the volume directory: {volume_dir}",
        )

    return True, normalized_path, ""


@tool
def read_file(file_path: str) -> str:
    """Read the content of a file and return it as a string.

    The file must be located within the volume directory.

    Args:
        file_path: Path to the file to read (relative to volume directory)

    Returns:
        The content of the file as a string, or an error message.
    """
    is_valid, abs_path, error_msg = get_volume_path(file_path)

    if not is_valid:
        return error_msg

    try:
        # Check if the file exists
        if not os.path.exists(abs_path):
            return f"Error: File does not exist: {file_path}"

        # Check if it's a file (not a directory)
        if not os.path.isfile(abs_path):
            return f"Error: Not a file: {file_path}"

        # Read the file
        with open(abs_path) as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def create_file(file_name: str, content: str, subfolder: str = "") -> str:
    """Create a file inside the volume folder.

    Args:
        file_name: Name of the file to create (e.g., "config.json", "data.txt")
        content: Content to write to the file
        subfolder: Optional subfolder inside volume directory (e.g., "project1")

    Returns:
        A message indicating success or failure
    """
    try:
        # Get the path to the volume directory
        is_valid, volume_dir, error_msg = get_volume_path()

        if not is_valid:
            return error_msg

        # Create subfolder if provided
        if subfolder:
            is_valid, subfolder_path, error_msg = get_volume_path(subfolder)

            if not is_valid:
                return error_msg

            output_dir = subfolder_path
        else:
            output_dir = volume_dir

        # Create the directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Create the file path
        file_path = os.path.join(output_dir, file_name)

        # Write the content to the file
        with open(file_path, "w") as f:
            f.write(content)

        return f"Successfully created file: {file_path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"


@tool
def list_files(directory_path: str = "") -> str:
    """List all files and directories in the specified path within the volume directory.

    If no path is provided, it will list files in the volume directory.

    Args:
        directory_path: Path to list files from (relative to volume). If empty, defaults to volume directory.

    Returns:
        A formatted string listing all files and directories, or an error message.
    """
    try:
        # Validate the requested directory path
        is_valid, abs_path, error_msg = get_volume_path(directory_path)

        if not is_valid:
            return error_msg

        # Check if directory exists
        if not os.path.exists(abs_path):
            return f"Error: Directory '{directory_path}' does not exist."

        if not os.path.isdir(abs_path):
            return f"Error: '{directory_path}' is not a directory."

        # Get list of all files and directories
        items = os.listdir(abs_path)

        # Group by type (directory or file)
        directories = []
        files = []

        for item in items:
            item_path = os.path.join(abs_path, item)
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
        display_path = directory_path if directory_path else "volume/"
        result = f"Contents of '{display_path}':\n\n"

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
