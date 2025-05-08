import datetime
import json
import math
import uuid
from dataclasses import asdict
from enum import Enum
from typing import Optional

from langchain_core.messages import BaseMessage
from langsmith import RunTree
from langsmith.client import Client
from langsmith.evaluation import EvaluationResult
from langsmith.evaluation._arunner import AsyncExperimentResults
from pydantic import BaseModel
from termcolor import colored


class _CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dataclass_fields__"):  # Check if obj is a dataclass
            return asdict(obj)
        elif isinstance(obj, RunTree):
            return obj.dict()
        elif isinstance(obj, BaseMessage):
            return obj.model_dump()
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, EvaluationResult):
            return obj.dict()
        elif isinstance(obj, Client):  # Handle LangSmith Client
            return {
                "api_url": obj.api_url,
                "tenant_id": str(obj._tenant_id)
                if hasattr(obj, "_tenant_id")
                else None,
            }
        return super().default(obj)


class Verbosity(Enum):
    """Defines evaluation result verbosity."""

    SCORE = 0
    SCORE_DETAILED = 1
    FULL = 2


async def print_evaluation(
    results: AsyncExperimentResults,
    client: Optional[Client] = None,
    *,
    verbosity: Verbosity = Verbosity.SCORE_DETAILED,
    dump_file: Optional[str] = None,
):
    """Print AsyncEvaluationResults.
    Computes the experiment URL if client is provided
    """
    dataset_id = None
    parsed = []

    async for result in results:
        if dataset_id is None:
            dataset_id = result["example"].dataset_id

        parsed_result = {}
        for root_k, root_v in result.items():
            value = dict(root_v)
            parsed_result[root_k] = value
        parsed.append(parsed_result)

    experiment_url = None
    if client is not None:
        experiment_name = results.experiment_name
        organization_id = "265bce82-15be-4d5e-9ae9-55d5e7b4e96e"
        session_id = client.read_project(project_name=experiment_name).id
        experiment_url = f"https://smith.langchain.com/o/{organization_id}/datasets/{dataset_id}/compare?selectedSessions={session_id}"

    data_json = json.dumps(
        {
            "url": experiment_url,
            "results": parsed,
        },
        cls=_CustomEncoder,
    )

    # Output to file
    if dump_file is not None:
        with open(dump_file, "w") as f:
            f.write(data_json)

    data = json.loads(data_json)
    _print_evaluation_result(data, verbosity)


def _print_evaluation_result(eval_results: dict, verbose: Verbosity):
    def round_half_up(n):
        """Rounds a number up if its decimal part is 0.5 or greater."""
        if n % 1 == 0:  # Check if n is an integer return n
            return n
        return math.ceil(n + 1e-10)

    def round_to(number, decimal_places=2):
        """Rounds a number to the specified number of decimal places, rounding half up."""
        scale = 10**decimal_places
        return round_half_up(number * scale) / scale

    experiment_url = eval_results["url"]
    results = eval_results["results"]

    if verbose == Verbosity.SCORE:
        data = {
            "score": 0.0,
            "parts": [],
        }
        for result in results:
            eval_result = result["evaluation_results"]["results"][-1]  # get last result
            data["score"] += float(eval_result["score"])
            data["parts"].append(
                {"score": eval_result["score"], "id": eval_result["source_run_id"]}
            )
        avg_score = round_to(data["score"] / len(results), 2)
        avg_score_str = f"{avg_score:.2f}"
        print("=" * 16)
        print(f"∥ score: {colored(avg_score_str, 'green')}  ∥")
        print("=" * 16)

        print(
            f"\n{colored('Link', 'light_magenta', attrs=['bold'])}: {colored(experiment_url, 'light_magenta', attrs=['underline'])}"
        )

    elif verbose == Verbosity.SCORE_DETAILED:
        data = {
            "score": 0.0,
            "parts": {},
        }
        for result in results:
            eval_result = result["evaluation_results"]["results"][-1]  # get last result
            example_id = result["run"]["reference_example_id"]
            data["score"] += float(eval_result["score"])
            if example_id not in data["parts"]:
                data["parts"][example_id] = []
            data["parts"][example_id].append(
                {"score": eval_result["score"], "id": eval_result["source_run_id"]}
            )
        avg_score = round_to(data["score"] / len(results), 2)
        avg_score_str = f"{avg_score:.2f}"
        print(f"score: {colored(avg_score_str, 'green')}")
        for ref_example_id, part in data["parts"].items():
            part_sum = round_to(sum(p["score"] for p in part) / len(part), 2)
            print(
                f"         └── {colored(f'{part_sum:.2f}', 'grey')}       ({colored(ref_example_id, 'grey')})"
            )
            for rep_part in part:
                score = rep_part["score"]
                print(
                    f"               └── {colored(f'{score:.2f}', 'grey')} ({colored(rep_part['id'], 'grey')})"
                )

        print(
            f"\n{colored('Link', 'light_magenta', attrs=['bold'])}: {colored(experiment_url, 'light_magenta', attrs=['underline'])}"
        )
        return

    elif verbose == Verbosity.FULL:
        for result in results:
            run = result["run"]
            eval_result = result["evaluation_results"]["results"][-1]  # get last result

            print(
                f"{colored('run', 'cyan')}#{colored(run['id'], 'cyan')} [score: {colored(eval_result['score'], 'green')}] ({run['extra']['metadata']['num_repetitions']} reps)"
            )

            print("== Input ==")
            for msg in run["inputs"]["inputs"]["messages"]:
                print(
                    f"\t{colored(msg['role'], 'yellow'):<18}: {colored(msg['content'], 'grey')}"
                )

            print("== Output ==")
            print(
                f"\t{colored('ai', 'yellow'):<18}: {colored(run['outputs']['output'], 'grey')}"
            )

            print("== Reference Output ==")
            msg_out = result["example"]["outputs"]["message"]
            print(
                f"\t{colored(msg_out['role'], 'yellow'):<18}: {colored(msg_out['content'], 'grey')}"
            )

            print("== Evaluation ==")
            print(f"\t{colored(eval_result['comment'], 'grey')}")
            print("---" * 30)

        print(
            f"\n{colored('Link', 'light_magenta', attrs=['bold'])}: {colored(experiment_url, 'light_magenta', attrs=['underline'])}"
        )


__all__ = [
    print_evaluation.__name__,
    Verbosity.__name__,
]


if __name__ == "__main__":
    with open("data2.json") as f:
        # print(json.load(f))
        _print_evaluation_result(json.load(f), Verbosity.SCORE)
