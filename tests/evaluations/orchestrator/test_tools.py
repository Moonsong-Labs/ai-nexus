import pytest
from datasets.orchestrator_dataset import DATASETS
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langsmith.client import Client
from langsmith.evaluation import EvaluationResults
from termcolor import colored
from testing.inputs import decode_base_messages
from testing.utils import get_list_diff, round_to

from common.state import Project
from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State


@pytest.mark.asyncio
async def test_correctness() -> None:
    dataset_name = DATASETS.orchestrator_tool_usage.name

    client = Client()

    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )
    config = orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}})

    async def run(inputs: dict):
        messages = decode_base_messages(inputs["messages"])
        project = Project(**inputs["project"]) if "project" in inputs else None

        result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
            State(
                messages=messages,
                project=project,
            ),
            config,
            store=orchestrator.store,
        )

        last_message = result["messages"][-1]
        return {"tools": [t["name"] for t in getattr(last_message, "tool_calls", [])]}

    def tool_usage_correctness(inputs, outputs, reference_outputs):
        missing, extra = get_list_diff(reference_outputs["tools"], outputs["tools"])
        return EvaluationResults(
            results=[
                {"key": k, "score": v}
                for k, v in calculate_score(
                    len(missing), len(extra), len(reference_outputs["tools"])
                ).items()
            ]
        )

    results = await client.aevaluate(
        run,
        data=dataset_name,
        evaluators=[tool_usage_correctness],
        experiment_prefix=f"{orchestrator.name.lower()}-{orchestrator.agent_config.model}-heuristic-evaluation",
        num_repetitions=3,
        max_concurrency=4,
    )

    grouped_scores = {}
    async for result in results:
        if result["example"].id not in grouped_scores:
            grouped_scores[result["example"].id] = []

        score = {}
        for evaluation_result in result["evaluation_results"]["results"]:
            score[evaluation_result.key] = evaluation_result.score
        grouped_scores[result["example"].id].append(score)

    # print and evaluate output
    failed = False
    failure_threshold = 0.75
    print()
    for example_id, example_scores in grouped_scores.items():
        print(f"== {example_id} ==")
        keys = example_scores[0].keys()

        for key in keys:
            print(f"{colored(key, 'yellow'):<20} ", end="")
            total_score = 0.0

            for score in example_scores:
                value = score[key]
                total_score += value
                print(
                    f"{colored(value, 'green') if value else colored(value, 'red'):<15}",
                    end="",
                )

            avg_score = round_to(total_score / len(example_scores), 2)
            avg_score_str = f"{avg_score:.2f}"
            if key == "f1_score":
                failed = failed or avg_score < failure_threshold

            print(f"{colored(avg_score_str, 'cyan'):>8}")

    if failed:
        pytest.fail(
            f"Not all average f1 scores were above {failure_threshold} in all examples"
        )


def calculate_score(num_missing, num_extra, num_total) -> dict[str, float]:
    # handle case for empty tool calls
    if num_total == 0 and num_missing == 0 and num_extra == 0:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1_score": 1.0,
        }

    fp = num_extra
    fn = num_missing
    tp = num_total - num_missing

    precision = 0.0 if tp == 0.0 else tp / (tp + fp)
    recall = 0.0 if tp == 0.0 else tp / (tp + fn)
    f1_score = (
        0.0
        if precision * recall == 0.0
        else 2 * (precision * recall) / (precision + recall)
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
    }
