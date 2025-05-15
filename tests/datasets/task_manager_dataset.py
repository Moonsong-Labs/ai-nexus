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
                    "content": "I need a project name to start. Once you provide the project name, I will look for the project files in the volume directory and begin the planning process."
                }
            },
        },
        {
            "inputs": {
                "messages": [
                    {
                        "role": "human",
                        "content": "What files must I provide to you?",
                    }
                ]
            },
            "outputs": {
                "message": {
                    "content": "You need to provide eight specific files within the project directory. These are: projectRequirements.md, techContext.md, systemPatterns.md, testingContext.md, projectbrief.md, featuresContext.md, securityContext.md and progress.md"
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
