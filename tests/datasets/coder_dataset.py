from typing import TypedDict

from langsmith import Client

CODER_DATASET_NAME = "coder-test-dataset"


class CodeEvaluatorInputs(TypedDict):
    starting_code: dict
    user_input: str


class CodeEvaluatorReferenceOutputs(TypedDict):
    expectations: str


def create_dataset():
    examples = [
        {
            "inputs": CodeEvaluatorInputs(
                user_input="Create a python JSON REST API server with a root entry point",
                starting_code={},
            ),
            "outputs": CodeEvaluatorReferenceOutputs(
                expectations="The agent should have created a JSON REST API server with a '/hello' entry point. If it added dependencies, it should have added them to the proper dependencies file"
            ),
        }
    ]

    client = Client()

    dataset = client.create_dataset(
        dataset_name=CODER_DATASET_NAME,
    )

    client.create_examples(dataset_id=dataset.id, examples=examples)


if __name__ == "__main__":
    create_dataset()
