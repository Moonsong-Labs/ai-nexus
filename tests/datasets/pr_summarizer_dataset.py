from langsmith import Client

PR_SUMMARIZER_DATASET_NAME = "Pr-summarizer-samples-dataset"


def create_dataset():
    client = Client()

    dataset = client.create_dataset(
        dataset_name=PR_SUMMARIZER_DATASET_NAME,
        description="A sample dataset for PR Summarizer in LangSmith.",
    )

    # Create examples - using a direct input format
    examples = [
        {
            "inputs": {
                "repository": "Moonsong-Labs/ai-nexus",
                "pr_num": "101",
            },
            "outputs": {
                "output":
"""diff --git a/project_memories/global.md b/project_memories/global.md
index 998e61e..2d7b74e 100644
--- a/project_memories/global.md
+++ b/project_memories/global.md
@@ -76,7 +76,7 @@ This file outlines the overarching standards and technological choices for the A
     *   **uv:** Used for managing Python virtual environments and installing packages.
     *   **python-dotenv:** Manages environment variables from `.env` files.
 *   **Development Workflow & Build:**
-    *   **Make:** Used as a task runner to automate common commands.
+    *   **Make:** Used as a task runner to automate common commands (e.g., `deps`, `lint`, `test`, `ci-build-check` (NEW)).
     *   **gcloud:** Deployment of services.
     *   **Local Demo Script (NEW):** `uv run --env-file .env -- python ./src/demo/orchestrate.py exec ai`
 *   **Testing & Code Quality:**
@@ -89,7 +89,9 @@ This file outlines the overarching standards and technological choices for the A
     *   **codespell:** Checks for spelling mistakes.
     *   **openevals:** Used for custom evaluation logic, particularly for the Coder agent.
     *   **debugpy:** Development dependency for remote debugging support.
-    *   **CI Pipeline (`.github/workflows/checks.yml`):** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
+    *   **CI Pipeline:**
+        *   **`checks.yml`:** Runs linting (Ruff, codespell), unit tests (`make test_unit`), and Coder integration tests (`make test_coder`). The Coder tests job requires `GOOGLE_API_KEY` as a secret.
+        *   **`compile-check.yml` (NEW):** Runs a graph compilation check (`make ci-build-check`) on pushes and PRs to `main`. This job requires `GEMINI_API_KEY` as a secret.
 *   **Version Control:** Git.
 *   **LLM Models:**
     *   **`gemini-1.5-flash-latest` / `gemini-2.5-flash-preview-04-17` (or similar flash variants):** Preferred for simple tasks, quick evaluations. (`agent_template` default model inherited from `AgentConfiguration` if not overridden, `AgentConfiguration` defaults to `gemini-2.0-flash`). The Code Reviewer agent uses `gemini-2.0-flash`.
@@ -422,9 +424,10 @@ ai-nexus/
 │   └── launch.json
 ├── .github/
 │   └── workflows/
-│       └── checks.yml
+│       ├── checks.yml
+│       ├── compile-check.yml     # ADDED
 │       └── update_project_memory.yml
-├── Makefile
+├── Makefile                      # UPDATED: Added ci-build-check target
 ├── README.md                     # UPDATED: Examples for semantic memory, new config, local demo
 ├── agent_memories/
 │   └── grumpy/"""
            },
        },
    ]

    # Add examples to the dataset
    client.create_examples(dataset_id=dataset.id, examples=examples)

    return dataset


# Only create the dataset when this script is run directly
if __name__ == "__main__":
    create_dataset()
