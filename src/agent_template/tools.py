"""Generic utility tools for the agent."""

import os
from pathlib import Path
from typing import Optional

from langchain_core.tools import Tool

from common.logging import get_logger

logger = get_logger(__name__)


def create_file_dump_tool() -> Tool:
    """Create a tool that dumps any arbitrary text to a file.

    Returns:
        Tool: A tool that writes content to a file
    """

    def file_dump(
        content: str, output_path: str, filename: Optional[str] = None
    ) -> bool:
        """Write content to a file in the specified directory.

        Args:
            content: The text content to write to the file
            output_path: Directory path where the file will be saved
            filename: Optional filename (if None, a default name will be used)

        Returns:
            bool: True if successful, False if failed
        """
        try:
            # Create the output directory if it doesn't exist
            dir_path = Path(output_path)
            os.makedirs(dir_path, exist_ok=True)

            # Use provided filename or create a default one
            if not filename:
                filename = "file_dump.txt"

            file_path = dir_path / filename

            # Write content to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True
        except Exception as e:
            logger.error(f"Error writing to file: {str(e)}")
            return False

    return Tool(
        name="file_dump",
        description="Write content to a file in the specified directory",
        func=file_dump,
    )
