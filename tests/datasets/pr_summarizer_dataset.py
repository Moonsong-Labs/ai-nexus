from langsmith import Client

from typing import Optional

import os, json, fnmatch

PR_SUMMARIZER_DATASET_NAME = "Pr-summarizer-samples-dataset"

def create_dataset(*, force: Optional[bool] = False):
    client = Client()

    if force and client.has_dataset(dataset_name=PR_SUMMARIZER_DATASET_NAME):
        client.delete_dataset(dataset_name=PR_SUMMARIZER_DATASET_NAME)

    dataset = client.create_dataset(
        dataset_name=PR_SUMMARIZER_DATASET_NAME,
        description="A sample dataset for PR Summarizer in LangSmith.",
    )

    examples = []

    dataset_path = os.path.join(os.curdir, 'tests', 'datasets', 'summarizer')
    for filename in os.listdir(dataset_path):
        if fnmatch.fnmatch(filename, '*.json'):
            file = os.path.join(dataset_path, filename)
            with open(file, "r") as f:
                examples.append(json.load(f))

    # Add examples to the dataset
    client.create_examples(dataset_id=dataset.id, examples=examples)

    return dataset


# Only create the dataset when this script is run directly
if __name__ == "__main__":
    create_dataset(force=True)
