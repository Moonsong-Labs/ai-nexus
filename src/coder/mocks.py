class MockGithubApi:
    branches = ["main"]
    active_branch = "main"
    # Mock file system structure: {type: "dir"|"file", content: str|dict}
    files = {
        "type": "dir",
        "content": {}
    }
    # Store the current pull request: {title: str, body: str, head: str, base: str}
    pull_request = None
    # Track file operations: [{type: str, args: dict}]
    operations = []

    def set_active_branch(self, branch_name: str):
        if branch_name in self.branches:
            self.active_branch = branch_name
            return f"Switched to branch `{branch_name}`"
        else:
            return (
                f"Error {branch_name} does not exist,"
                f"in repo with current branches: {str(self.branches)}"
            )

    def create_branch(self, proposed_branch_name: str) -> str:
        """Create a new branch, and set it as the active bot branch.
        If the proposed branch already exists, we append _v1 then _v2...
        until a unique name is found."""
        i = 0
        new_branch_name = proposed_branch_name
        
        for i in range(1000):
            if new_branch_name not in self.branches:
                self.branches.append(new_branch_name)
                self.active_branch = new_branch_name
                return (
                    f"Branch '{new_branch_name}' "
                    "created successfully, and set as current active branch."
                )
            i += 1
            new_branch_name = f"{proposed_branch_name}_v{i}"
            
        return (
            "Unable to create branch. "
            "At least 1000 branches exist with named derived from "
            f"proposed_branch_name: `{proposed_branch_name}`"
        )

    def _get_files_recursive(self, current_path: str, node: dict) -> list:
        """Helper function to recursively get all files under a path."""
        files = []
        if node["type"] == "file":
            files.append(current_path)
        else:
            for name, child in node["content"].items():
                child_path = f"{current_path}/{name}" if current_path else name
                files.extend(self._get_files_recursive(child_path, child))
        return files

    def get_files_from_directory(self, directory_path: str) -> str:
        """Recursively fetches files from a directory in the repo."""
        # Split path into components
        path_parts = [p for p in directory_path.split("/") if p]
        
        # Navigate to the target directory
        current = self.files
        for part in path_parts:
            if current["type"] != "dir" or part not in current["content"]:
                return f"No files found in directory: {directory_path}"
            current = current["content"][part]
            
        if current["type"] != "dir":
            return f"Error: {directory_path} is not a directory"
            
        # Get all files under this directory
        files = self._get_files_recursive(directory_path, current)
        
        if not files:
            return f"No files found in directory: {directory_path}"
            
        return str(files)

    def create_pull_request(self, pr_query: str) -> str:
        """Creates a pull request from the bot's branch to the base branch."""
        if self.active_branch == "main":
            return "Cannot make a pull request because commits are already in the main branch."
            
        title = pr_query.split("\n")[0]
        body = pr_query[len(title) + 2 :]
        
        self.pull_request = {
            "title": title,
            "body": body,
            "head": self.active_branch,
            "base": "main"
        }
        
        return "Successfully created PR number 1"

    def create_file(self, file_query: str) -> str:
        """Creates a new file on the Github repo."""
        if self.active_branch == "main":
            return (
                "You're attempting to commit to the directly to the"
                f"{self.active_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        file_path = file_query.split("\n")[0]
        file_contents = file_query[len(file_path) + 2 :]

        self.operations.append({
            "type": "create",
            "args": {
                "path": file_path,
                "content": file_contents,
                "branch": self.active_branch
            }
        })
        
        return f"Created file {file_path}"

    def update_file(self, file_query: str) -> str:
        """Updates a file with new content."""
        if self.active_branch == "main":
            return (
                "You're attempting to commit to the directly"
                f"to the {self.active_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        file_path = file_query.split("\n")[0]
        old_content = file_query.split("OLD <<<<")[1].split(">>>> OLD")[0].strip()
        new_content = file_query.split("NEW <<<<")[1].split(">>>> NEW")[0].strip()

        self.operations.append({
            "type": "update",
            "args": {
                "path": file_path,
                "old_content": old_content,
                "new_content": new_content,
                "branch": self.active_branch
            }
        })
        
        return f"Updated file {file_path}"

    def delete_file(self, file_path: str) -> str:
        """Deletes a file from the repo."""
        if self.active_branch == "main":
            return (
                "You're attempting to commit to the directly"
                f"to the {self.active_branch} branch, which is protected. "
                "Please create a new branch and try again."
            )

        self.operations.append({
            "type": "delete",
            "args": {
                "path": file_path,
                "branch": self.active_branch
            }
        })
        
        return f"Deleted file {file_path}"

    def read_file(self, file_path: str) -> str:
        """Read a file from the repo."""
        # Split path into components
        path_parts = [p for p in file_path.split("/") if p]
        
        # Navigate to the target file
        current = self.files
        for part in path_parts:
            if current["type"] != "dir" or part not in current["content"]:
                return f"File not found `{file_path}`"
            current = current["content"][part]
            
        if current["type"] != "file":
            return f"Error: {file_path} is not a file"
            
        return current["content"] 