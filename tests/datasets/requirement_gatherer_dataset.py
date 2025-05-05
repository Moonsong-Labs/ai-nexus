from langsmith import Client

client = Client()

REQUIREMENT_GATHERER_DATASET_NAME = "Requirement-gatherer-naive-dataset-testing-2"
dataset = client.create_dataset(
    dataset_name=REQUIREMENT_GATHERER_DATASET_NAME, description="A sample dataset in LangSmith."
)

# Create examples - using a direct input format
examples = [
    {
        "inputs": {
            "messages": [
                {"role": "human", "content": "Start the requirement gathering process"}
            ]
        },
        "outputs": {
            "message": {
                "content": "Hello! I'm the Product-Requirement Gatherer. To start, could you please describe the overall vision for your project? Also, is this a full product development effort or more of a hobby/smaller project?"
            }
        },
    },
]

# Add examples to the dataset
client.create_examples(dataset_id=dataset.id, examples=examples)