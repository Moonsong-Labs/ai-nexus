"""Tool for reading task planning files from a project."""

import glob
import logging
import os
from typing import Callable

from langchain_core.tools import tool

# Set up logger for this module
logger = logging.getLogger(__name__)


def create_read_task_planning_tool(use_stub: bool) -> Callable:
    """Create a read_task_planning tool that can read task planning files from a project or return a default for stubs.

    Args:
        use_stub: Whether to use the stub version of the tool

    Returns:
        A tool function that can read task planning files or return a default for stubs
    """

    @tool("read_task_planning", parse_docstring=True)
    def read_task_planning(project_name: str) -> str:
        """Read the content of a task planning file matching the pattern task-01*.

        When running with stubs, returns a default task planning content.

        Args:
            project_name: Name of the project to read the task planning file from

        Returns:
            The content of the task planning file as a string, or a default task when using stubs.
        """
        # If using stubs, return a default task planning content
        if use_stub:
            logger.info(
                f"Using stub for project '{project_name}'. Returning default task planning."
            )
            return """# Task Planning for Stub Project
            
Task: Implement this awesome feature
"""

        # Otherwise, proceed with the actual file reading logic
        try:
            pattern = os.path.join("projects", project_name, "planning", "task-01*")

            # Find files matching the pattern
            matching_files = glob.glob(pattern)

            # Check if any files were found
            if not matching_files:
                return f"Error: No files matching pattern '{pattern}' found"

            # If multiple files match, use the first one and warn
            if len(matching_files) > 1:
                logger.warning(
                    f"Multiple files match pattern '{pattern}'. Using the first one: {matching_files[0]}"
                )

            file_path = matching_files[0]

            # Check if the file exists (should always be true, but good practice)
            if not os.path.exists(file_path):
                return f"Error: File does not exist: {file_path}"

            # Check if it's a file (not a directory)
            if not os.path.isfile(file_path):
                return f"Error: Not a file: {file_path}"

            # Read the file
            with open(file_path, encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            return f"Error reading task planning file: {e}"

    return read_task_planning
