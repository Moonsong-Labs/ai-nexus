# Project Scripts

This directory contains utility scripts for the project.

## Scripts

### 1. `fetch_pr_details.sh`

*   **Purpose**: Fetches details of a given GitHub Pull Request, including its title, body, and diff.
*   **Usage**:
    ```bash
    ./fetch_pr_details.sh -r <owner/repo> -p <pr_number>
    # OR
    ./fetch_pr_details.sh -u <pr_url>
    ```
*   **Prerequisites**: `curl`, `jq`.
*   **Output**: Prints a formatted string containing the PR title, body, and diff to standard output.

### 2. `generate_project_memory.sh`

*   **Purpose**: Generates an initial project memory by scanning project files and using a Gemini model to synthesize the information.
*   **Usage**:
    ```bash
    ./generate_project_memory.sh -k <GEMINI_API_KEY> [-d <root_directory>] [-o <output_file>]
    ```
    *   `-k <GEMINI_API_KEY>`: Your Google AI Gemini API Key. Can also be set via `GOOGLE_API_KEY` or `GEMINI_API_KEY_ENV` environment variables.
    *   `-d <root_directory>`: (Optional) The root directory of the project to scan. Defaults to the parent directory of the `scripts` folder.
    *   `-o <output_file>`: (Optional) Path to save the generated memory. Defaults to `project_memories/global.md` relative to the script's location.
*   **Prerequisites**: `curl`, `jq`, `git`, `find`.
*   **Output**: Creates or updates the specified output file with the generated project memory.

### 3. `update_project_memory_from_pr.sh`

*   **Purpose**: Updates the project memory ([`project_memories/global.md`](project_memories/global.md:1) by default) based on the details of a specific Pull Request. It uses [`fetch_pr_details.sh`](scripts/fetch_pr_details.sh:1) to get PR information and then a Gemini model to update the memory.
*   **Usage**:
    ```bash
    ./update_project_memory_from_pr.sh -k <GEMINI_API_KEY> [-r <owner/repo> -p <pr_number> | -u <pr_url>]
    ```
    *   `-k <GEMINI_API_KEY>`: Your Google AI Gemini API Key. Can also be set via `GOOGLE_API_KEY` or `GEMINI_API_KEY_ENV` environment variables, or by placing it in a `.env` file in the script's directory.
    *   `-r <owner/repo> -p <pr_number>`: Specify the repository and PR number.
    *   `-u <pr_url>`: Alternatively, provide the full URL of the Pull Request.
*   **Prerequisites**: `curl`, `jq`, and [`fetch_pr_details.sh`](scripts/fetch_pr_details.sh:1) must be in the same directory and executable.
*   **Output**: Modifies the [`project_memories/global.md`](project_memories/global.md:1) file (or the file specified by `GLOBAL_MEMORY_FILE` within the script) with the updated memory. If the Gemini model suggests "NO CHANGE", the file is not modified.

## GitHub Actions Workflow

There is a GitHub Actions workflow located at [`.github/workflows/update_project_memory.yml`](.github/workflows/update_project_memory.yml:1) that utilizes the [`update_project_memory_from_pr.sh`](scripts/update_project_memory_from_pr.sh:1) script. This workflow triggers automatically when a Pull Request is merged to the `main` branch or can be manually triggered. It updates the project memory and creates a new PR if changes are detected.

**Important**: For the GitHub Action and the scripts requiring API access, ensure the `GEMINI_API_KEY` is securely managed (e.g., using GitHub Secrets for the workflow, or environment variables/`.env` file for local execution).