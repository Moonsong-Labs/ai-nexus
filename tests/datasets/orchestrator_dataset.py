import inspect
import random
import sys
import uuid

from langsmith import Client


def uuid4_generator(seed):
    """
    Generates a deterministic UUID4 based on the seed value.

    Args:
        seed: The seed value for the pseudorandom number generator.

    Returns:
        A UUID object.
    """

    random.seed(seed)

    def gen() -> uuid.UUID:
        # Generate 16 random bytes
        random_bytes = bytes(random.randint(0, 255) for _ in range(16))

        # Set the version and variant bits according to RFC 4122
        random_bytes = bytearray(random_bytes)
        random_bytes[6] = (random_bytes[6] & 0x0F) | 0x40  # Version 4
        random_bytes[8] = (random_bytes[8] & 0x3F) | 0x80  # Variant RFC4122

        return uuid.UUID(bytes=bytes(random_bytes))

    return gen


def create_orchestrator_tool_usage_dataset(dataset_name: str, recreate: bool = False):
    uuid4 = uuid4_generator(dataset_name)

    examples = [
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "Hi",
                        "role": "human",
                    },
                ],
            },
            "outputs": {
                "tools": [],
            },
        },
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "Start now",
                        "role": "human",
                    },
                ],
            },
            "outputs": {
                "tools": ["requirements"],
            },
        },
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "Let's start a project now",
                        "role": "human",
                    },
                ],
            },
            "outputs": {
                "tools": ["requirements"],
            },
        },
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "I want to finalize some requirements for a new project",
                        "role": "human",
                    },
                ],
            },
            "outputs": {
                "tools": ["requirements"],
            },
        },
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "I want to build a website",
                        "role": "human",
                    },
                ],
            },
            "outputs": {
                "tools": ["requirements"],
            },
        },
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "I want to build a project",
                        "role": "human",
                    },
                ],
            },
            "outputs": {
                "tools": ["requirements"],
            },
        },
        {
            "id": uuid4(),
            "inputs": {
                "messages": [
                    {
                        "content": "I want to build a website",
                        "role": "human",
                    },
                    {
                        "content": "Okay, let's start by gathering the requirements for the website. I'll delegate this task to the Requirements Gatherer.",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "requirements",
                                "args": {"content": "website"},
                                "id": "1",
                            }
                        ],
                    },
                    {
                        "content": "# Project: MyWebsite\nMyWebsite is a personal blog intended for sharing personal experiences with friends and family.",
                        "role": "tool",
                        "name": "requirements",
                        "tool_call_id": "1",
                        "status": "success",
                    },
                ],
                "project": {
                    "id": "project-0",
                    "name": "test",
                    "path": "/tmp/project-0",
                },
            },
            "outputs": {
                "tools": ["architect"],
            },
        },
    ]

    # if an example is deleted we cannot recreate it with same uuid, neither update it,
    # in this case we need to mark it as yanked manually, or recreate entire dataset.
    yanked_example_ids = []

    client = Client()

    if recreate:
        client.delete_dataset(dataset_name=dataset_name)
        print(f"[{dataset_name}] deleted dataset")

    if not client.has_dataset(dataset_name=dataset_name):
        client.create_dataset(dataset_name)
        print(f"[{dataset_name}] created dataset")

    update_examples = []
    create_examples = []
    existing_example_ids = [
        example.id for example in client.list_examples(dataset_name=dataset_name)
    ]

    for example in examples:
        if example["id"] in existing_example_ids:
            update_examples.append(example)
        elif example["id"] not in yanked_example_ids:
            create_examples.append(example)

    num_updated = (
        client.update_examples(dataset_name=dataset_name, updates=update_examples)[
            "count"
        ]
        if update_examples
        else 0
    )

    num_created = (
        client.create_examples(dataset_name=dataset_name, examples=create_examples)[
            "count"
        ]
        if create_examples
        else 0
    )
    print(
        f"[{dataset_name}] updated {num_updated} example(s), created {num_created} example(s)"
    )


def print_help_message(script_name):
    print(f"Usage: python {script_name} <dataset_name> [recreate]")
    print("\nArguments:")
    print(
        f"  <dataset_name>  The name of the dataset to process. Must be one of: {', '.join(DATASETS.keys())}"
    )
    print(
        "  recreate        (Optional) If specified, the entire dataset will be recreated."
    )
    sys.exit(1)


class Datasets:
    class Dataset:
        def __init__(self, name, handler):
            self._name = name
            self._handler = handler

        @property
        def name(self) -> str:
            return self._name

        def __str__(self):
            return self._name

        def __call__(self, recreate):
            return self._handler(self._name, recreate)

    _members = None  # cache class members

    # Define all datasets for orchestrator
    orchestrator_tool_usage = Dataset(
        "orchestrator-tool-usage", create_orchestrator_tool_usage_dataset
    )

    @classmethod
    def get_members(cls):
        if cls._members:
            return cls._members

        cls._members = {
            name: value
            for name, value in inspect.getmembers(Datasets)
            if not (name.startswith("_") or inspect.isroutine(value))
        }

        return cls._members

    def keys(self):
        return self.get_members().keys()

    def __contains__(self, key):
        return key in self.get_members()

    def __getitem__(self, key):
        return self.get_members()[key]


DATASETS = Datasets()

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print_help_message(sys.argv[0])
    dataset = args[0]
    recreate = len(args) > 1 and args[1] == "recreate"

    if dataset not in DATASETS:
        print(
            f"ERROR! invalid dataset name {dataset}\n\nallowed: {', '.join(DATASETS.keys())}"
        )
        sys.exit(1)

    DATASETS[dataset](recreate)
