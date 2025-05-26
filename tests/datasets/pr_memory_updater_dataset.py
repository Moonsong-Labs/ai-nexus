import json
from pathlib import Path
from typing import Optional

from langsmith import Client

PR_MEMORY_UPDATER_DATASET_NAME = "Pr-memory-updater-samples-dataset"


def create_dataset(*, force: Optional[bool] = False):
    client = Client()

    if force and client.has_dataset(dataset_name=PR_MEMORY_UPDATER_DATASET_NAME):
        client.delete_dataset(dataset_name=PR_MEMORY_UPDATER_DATASET_NAME)

    dataset = client.create_dataset(
        dataset_name=PR_MEMORY_UPDATER_DATASET_NAME,
        description="A sample dataset for PR Memory Updater in LangSmith.",
    )

    examples = []

    dataset_path = Path("tests/datasets/pr_memory_updater")
    for file in dataset_path.glob("*.json"):
        try:
            with open(file, "r") as f:
                examples.append(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise RuntimeError(f"Error processing {file}: {e}")

    # Add examples to the dataset
    client.create_examples(dataset_id=dataset.id, examples=examples)

    return dataset


# Only create the dataset when this script is run directly
if __name__ == "__main__":
    create_dataset(force=True)
