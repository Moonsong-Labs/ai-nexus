from langsmith import Client

TASK_MANAGER_DATASET_NAME = "task-manager-requirements"


def create_dataset():
    client = Client()

    dataset = client.create_dataset(
        dataset_name=TASK_MANAGER_DATASET_NAME,
        description="A sample dataset in LangSmith.",
    )

    examples = [
        {
            "inputs": {
                "messages": [
                    {
                        "role": "human",
                        "content": "What requirements do you need to make your work done?",
                    }
                ]
            },
            "outputs": {
                "message": {
                    "content": "In order to create a task planning, I need to have access to prd.md, techstack.md and split_criteria.md files."
                }
            },
        },
    ]

    # Add examples to the dataset
    client.create_examples(dataset_id=dataset.id, examples=examples)

    return dataset


# Only create the dataset when this script is run directly
if __name__ == "__main__":
    create_dataset()
