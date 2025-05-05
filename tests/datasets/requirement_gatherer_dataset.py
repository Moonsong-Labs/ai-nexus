from langsmith import Client

REQUIREMENT_GATHERER_DATASET_NAME = "Requirement-gatherer-naive-dataset2"

def create_dataset():
    client = Client()
    
    dataset = client.create_dataset(
        dataset_name=REQUIREMENT_GATHERER_DATASET_NAME, 
        description="A sample dataset in LangSmith."
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
                    "content": "Hello! This seems a good project to work!"
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