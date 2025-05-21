from langsmith import Client

REQUIREMENT_GATHERER_DATASET_NAME = "Requirement-gatherer-dataset-human-ai"
FIRST_MESSAGE = """
I want to build a **Hobby** project called 'Buen Fla Project'.\n
Its a Rust based stack (data structure).\n
The **vision** is "learning and having fun"\n
For the **functional requirements**, it just need to have pop, push and is_empty functions.\n
You can fill the rest with what you think important. **DONT ASK MORE QUESTIONS** 
"""


def create_dataset():
    client = Client()

    dataset = client.create_dataset(
        dataset_name=REQUIREMENT_GATHERER_DATASET_NAME,
        description="A sample dataset in LangSmith.",
    )

    # Create examples - using a direct input format
    examples = [
        {
            "inputs": {
                "messages": [
                    {
                        "role": "human",
                        "content": FIRST_MESSAGE,
                    }
                ]
            },
            "outputs": {
                "message": {"content": "Requirements are confirmed"}
            },
        },
    ]

    # Add examples to the dataset
    client.create_examples(dataset_id=dataset.id, examples=examples)

    return dataset


# Only create the dataset when this script is run directly
if __name__ == "__main__":
    create_dataset()
