import os
import shutil

import pytest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from common.tools.create_directory import create_directory
from common.tools.create_file import create_file
from common.tools.list_files import list_files
from common.tools.read_file import read_file
from common.tools.summarize import create_summarize_tool

# Test directory for file operations
TEST_DIR = "test_tools_dir"


@pytest.fixture(scope="module")
def setup_test_directory():
    """Create a test directory for file operations."""
    # Create the test directory
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    yield TEST_DIR

    # Clean up after tests
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


class TestReadFile:
    """Tests for the read_file tool."""

    def test_read_file_success(self, setup_test_directory):
        """Test successful file reading."""
        test_dir = setup_test_directory
        test_file = os.path.join(test_dir, "test_file.txt")
        test_content = "This is test content for read_file"

        # Create a file using the create_file function
        create_file.invoke({"file_path": test_file, "content": test_content})

        # Read the file using read_file
        result = read_file.invoke(test_file)

        # Verify the content
        assert result == test_content

    def test_read_file_not_exists(self):
        """Test reading a file that doesn't exist."""
        result = read_file.invoke("nonexistent_file.txt")
        assert "Error: File does not exist" in result

    def test_read_file_not_a_file(self, setup_test_directory):
        """Test reading a path that is not a file."""
        test_dir = setup_test_directory
        result = read_file.invoke(test_dir)
        assert "Error: Not a file" in result


class TestListFiles:
    """Tests for the list_files tool."""

    def test_list_files_success_with_files_and_dirs(self, setup_test_directory):
        """Test successful listing of files and directories."""
        test_dir = setup_test_directory

        # Create subdirectories
        subdir1 = os.path.join(test_dir, "subdir1")
        subdir2 = os.path.join(test_dir, "subdir2")
        create_directory.invoke(subdir1)
        create_directory.invoke(subdir2)

        # Create files
        create_file.invoke(
            {
                "file_path": os.path.join(test_dir, "file1.txt"),
                "content": "Small file content",
            }
        )
        create_file.invoke(
            {
                "file_path": os.path.join(test_dir, "file2.py"),
                "content": "Larger file content" * 100,
            }
        )  # Make it bigger

        # List the directory
        result = list_files.invoke(test_dir)

        # Verify the result
        assert "Contents of" in result
        assert "Directories:" in result
        assert "📁 subdir1/" in result
        assert "📁 subdir2/" in result
        assert "Files:" in result
        assert "📄 file1.txt" in result
        assert "📄 file2.py" in result

    def test_list_files_empty_directory(self, setup_test_directory):
        """Test listing an empty directory."""
        test_dir = setup_test_directory

        # Create an empty subdirectory
        empty_dir = os.path.join(test_dir, "empty_dir")
        create_directory.invoke(empty_dir)

        # List the empty directory
        result = list_files.invoke(empty_dir)

        # Verify the result
        assert "Directory is empty" in result

    def test_list_files_directory_not_exists(self):
        """Test listing a directory that doesn't exist."""
        result = list_files.invoke("nonexistent_dir")
        assert "Error: Directory 'nonexistent_dir' does not exist" in result

    def test_list_files_not_a_directory(self, setup_test_directory):
        """Test listing a path that is not a directory."""
        test_dir = setup_test_directory
        test_file = os.path.join(test_dir, "not_a_dir.txt")

        # Create a file
        create_file.invoke(
            {"file_path": test_file, "content": "This is a file, not a directory"}
        )

        # Try to list it as a directory
        result = list_files.invoke(test_file)

        # Verify the result
        assert "is not a directory" in result


class TestCreateDirectory:
    """Tests for the create_directory tool."""

    def test_create_directory_success(self, setup_test_directory):
        """Test successful directory creation."""
        test_dir = setup_test_directory
        new_dir = os.path.join(test_dir, "new_test_dir")

        # Create the directory
        result = create_directory.invoke(new_dir)

        # Verify the result and that the directory exists
        assert "Successfully created directory" in result
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

    def test_create_nested_directory(self, setup_test_directory):
        """Test creating nested directories."""
        test_dir = setup_test_directory
        nested_dir = os.path.join(test_dir, "parent", "child", "grandchild")

        # Create the nested directory
        result = create_directory.invoke(nested_dir)

        # Verify the result and that the directory exists
        assert "Successfully created directory" in result
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)


class TestCreateFile:
    """Tests for the create_file tool."""

    def test_create_file_success(self, setup_test_directory):
        """Test successful file creation."""
        test_dir = setup_test_directory
        test_file = os.path.join(test_dir, "new_file.txt")
        test_content = "This is test content for create_file"

        # Create the file
        result = create_file.invoke({"file_path": test_file, "content": test_content})

        # Verify the result
        assert "Successfully created file" in result

        # Verify the file exists and has the correct content
        assert os.path.exists(test_file)
        assert os.path.isfile(test_file)

        # Read the file to verify content
        with open(test_file, "r") as f:
            content = f.read()
        assert content == test_content

    def test_create_file_directory_not_exists(self, setup_test_directory):
        """Test creating a file in a directory that doesn't exist."""
        test_dir = setup_test_directory
        nonexistent_dir = os.path.join(test_dir, "nonexistent_dir")
        test_file = os.path.join(nonexistent_dir, "new_file.txt")

        # Try to create a file in a directory that doesn't exist
        result = create_file.invoke(
            {"file_path": test_file, "content": "This should fail"}
        )

        # Verify the result
        assert "Error: Directory" in result
        assert "does not exist" in result

    def test_create_file_overwrite(self, setup_test_directory):
        """Test overwriting an existing file."""
        test_dir = setup_test_directory
        test_file = os.path.join(test_dir, "overwrite_file.txt")

        # Create the file first
        create_file.invoke({"file_path": test_file, "content": "Original content"})

        # Overwrite the file
        new_content = "New overwritten content"
        result = create_file.invoke({"file_path": test_file, "content": new_content})

        # Verify the result
        assert "Successfully created file" in result

        # Read the file to verify content was overwritten
        with open(test_file, "r") as f:
            content = f.read()
        assert content == new_content


class TestSummarize:
    """Tests for the summarize tool."""

    @pytest.mark.asyncio
    async def test_create_summarize_tool(self, capsys):
        """Test creating and using a summarize tool."""
        agent_name = "TestAgent"
        summarize_tool = create_summarize_tool(agent_name)
        
        # Verify tool properties
        assert summarize_tool.name == "summarize"
        assert "summary" in summarize_tool.description.lower()
        
        # Test invoking the tool
        test_summary = "This is a test summary of the agent's work"
        result = await summarize_tool.ainvoke({
            "summary": test_summary,
            "tool_call_id": "test_call_123"
        })
        
        # Verify the result is a Command
        assert isinstance(result, Command)
        assert "messages" in result.update
        assert "summary" in result.update
        
        # Verify the summary was stored correctly
        assert result.update["summary"] == test_summary
        
        # Verify the tool message
        messages = result.update["messages"]
        assert len(messages) == 1
        assert isinstance(messages[0], ToolMessage)
        assert messages[0].content == test_summary
        assert messages[0].tool_call_id == "test_call_123"
        
        # Verify console output
        captured = capsys.readouterr()
        assert f"======= Summary for {agent_name} =======" in captured.out
        assert test_summary in captured.out
        assert "==========================================" in captured.out

    @pytest.mark.asyncio
    async def test_summarize_tool_with_different_agents(self, capsys):
        """Test that different agents have different summarize tools."""
        agent1_name = "Agent1"
        agent2_name = "Agent2"
        
        summarize1 = create_summarize_tool(agent1_name)
        summarize2 = create_summarize_tool(agent2_name)
        
        # Both should have the same tool name
        assert summarize1.name == summarize2.name == "summarize"
        
        # Test agent 1
        await summarize1.ainvoke({
            "summary": "Agent 1 summary",
            "tool_call_id": "call_1"
        })
        
        captured1 = capsys.readouterr()
        assert f"======= Summary for {agent1_name} =======" in captured1.out
        assert "Agent 1 summary" in captured1.out
        
        # Test agent 2
        await summarize2.ainvoke({
            "summary": "Agent 2 summary",
            "tool_call_id": "call_2"
        })
        
        captured2 = capsys.readouterr()
        assert f"======= Summary for {agent2_name} =======" in captured2.out
        assert "Agent 2 summary" in captured2.out

    @pytest.mark.asyncio
    async def test_summarize_empty_summary(self):
        """Test summarize tool with empty summary."""
        summarize_tool = create_summarize_tool("TestAgent")
        
        result = await summarize_tool.ainvoke({
            "summary": "",
            "tool_call_id": "empty_call"
        })
        
        # Should still return a valid Command even with empty summary
        assert isinstance(result, Command)
        assert result.update["summary"] == ""
        assert result.update["messages"][0].content == ""
