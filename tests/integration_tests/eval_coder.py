import uuid
from typing import TypedDict

import pytest
from datasets.coder_dataset import (
    CODER_DATASET_NAME,
    CodeEvaluatorInputs,
    CodeEvaluatorReferenceOutputs,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langsmith import aevaluate
from openevals.types import EvaluatorResult
from openevals.utils import _arun_evaluator

from coder.graph import coder_new_pr_config
from coder.state import State
from coder.tools import get_github_tools
from common.components.github_mocks import MockGithubApi

EVAL_PROMPT = """You are an expert code reviewer.
Provided a starting code, user input and a set of expectations, your job is to grade the quality of a coder agent's
changes when acomplishing a required task.
The code is submitted in the form of a GitHub pull request. You will get a list of in order messages and tool calls
the coder made

<Rubric>
  An accurate trajectory:
    - Will have created a branch.
    - Will have changes that satisfy all expectations detailed in <expectations>.
    - Will not have changes unrelated to the <expectations>.
    - Will not introduce bugs.
</Rubric>

Based on the following starting_code (describes the initial project files) and expectations (describes the desired changes) :

<starting_code>
{starting_code}
</starting_code>

<expectations>
{expectations}
</expectations>

Grade this actual trajectory:

<trajectory>
{outputs}
</trajectory>

You should give a score between 0 and 1 and explain your reasoning. If any of the items in <Rubric> are not met, your score should be 0.5 or lower.
You should justify how the each expectation in <expectations> was met. If you have the slightest doubt about them being met fully then they are not met.
For example:
 - If the trajectory does not create a branch, your score should be 0.5 or lower even though the code is correct.
 - If the trajectory follows the correct steps but does not exactly comply with <expectations>, your score should be 0.5 or lower. Even if the deviations are minor.
 - If the app created an endpoint for an api in '/' but the expectations say it should have created a '/entry' endpoint, then expectations are NOT met. Score should be lower than 0.5
"""


class Result(TypedDict):
    score: float
    comment: str


judge_llm = init_chat_model(
    "google_genai:gemini-2.0-flash", temperature=0
).with_structured_output(Result)


async def evaluate_code_scorer(
    inputs: CodeEvaluatorInputs,
    outputs: str,
    reference_outputs: CodeEvaluatorReferenceOutputs,
) -> tuple[float, str]:
    ret = judge_llm.invoke(
        EVAL_PROMPT.format(
            starting_code=inputs["starting_code"],
            expectations=reference_outputs["expectations"],
            outputs=outputs,
        )
    )

    return (ret["score"], ret["comment"])


async def evaluate_code(
    inputs: CodeEvaluatorInputs,
    outputs: str,
    reference_outputs: CodeEvaluatorReferenceOutputs,
) -> EvaluatorResult:
    ret = await _arun_evaluator(
        run_name="coder",
        scorer=evaluate_code_scorer,
        feedback_key="coder",
        inputs=inputs,
        outputs=outputs,
        reference_outputs=reference_outputs,
    )
    print(ret)
    return ret


async def invoke_agent(inputs: CodeEvaluatorInputs) -> dict:
    mock_api = MockGithubApi()
    github_tools = get_github_tools(mock_api)
    mock_api.files = inputs["starting_code"]

    # Create and build graph
    graph = coder_new_pr_config().graph_builder(github_tools).compile()

    result = await graph.ainvoke(
        State(messages=[HumanMessage(content=inputs["user_input"])]),
        config={
            "configurable": {"thread_id": str(uuid.uuid4())},
        },
    )

    return result


@pytest.mark.asyncio
async def test_coder_run_eval_dataset():
    await aevaluate(invoke_agent, CODER_DATASET_NAME, evaluators=[evaluate_code])
