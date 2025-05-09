import uuid
from typing import TypedDict

import pytest
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from openevals.types import EvaluatorResult
from openevals.utils import _arun_evaluator

from coder.graph import graph_builder
from coder.mocks import MockGithubApi
from coder.state import State
from coder.tools import get_github_tools


@pytest.mark.asyncio(loop_scope="session")
async def test_coder_creates_hello_world():
    mock_api = MockGithubApi()
    github_tools = get_github_tools(mock_api)

    # Create and build graph
    graph = graph_builder(github_tools).compile()

    # Run agent with request to create main.py
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Create a main.py entry point that prints 'Hello World'",
                }
            ]
        },
        config,
    )

    # Verify main.py was created with correct content
    create_file_ops = [op for op in mock_api.operations if op["type"] == "create"]
    assert len(create_file_ops) > 0, "No file creation operation found"
    main_py_op = next(op for op in create_file_ops if op["args"]["path"] == "main.py")
    assert "Hello World" in main_py_op["args"]["content"]


@pytest.mark.asyncio(loop_scope="session")
async def test_coder_renames_function():
    # Setup mock GitHub API
    mock_api = MockGithubApi()
    mock_api.files = {
        "type": "dir",
        "content": {
            "math.py": {
                "type": "file",
                "content": "def sum_two_numbers(a, b):\n    return a + b",
            }
        },
    }
    github_tools = get_github_tools(mock_api)

    # Create and build graph
    graph = graph_builder(github_tools).compile()

    # Run agent with request to rename function
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Rename the sum_two_numbers function in math.py to add",
                }
            ]
        },
        config,
    )

    # Verify math.py was updated correctly
    update_ops = [op for op in mock_api.operations if op["type"] == "update"]
    assert len(update_ops) > 0, "No update operation found"

    math_update = next(op for op in update_ops if op["args"]["path"] == "math.py")
    assert "add" in math_update["args"]["new_content"]
    assert "sum_two_numbers" not in math_update["args"]["new_content"]


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
For example:
 - if the trajectory does not create a branch, your score should be 0.5 or lower even though the code is correct.
 - if the trajectory follows the correct steps but does not exactly comply with <expectations>, your score should be 0.5 or lower. Even if the deviations are minor.
"""


class Result(TypedDict):
    score: float
    comment: str


class CodeEvaluatorInputs(TypedDict):
    starting_code: str


class CodeEvaluatorReferenceOutputs(TypedDict):
    expectations: str


async def evaluate_code_scorer(
    inputs: CodeEvaluatorInputs,
    outputs: str,
    reference_outputs: CodeEvaluatorReferenceOutputs,
) -> EvaluatorResult:
    judge_llm = init_chat_model(
        "google_genai:gemini-2.0-flash", temperature=0
    ).with_structured_output(Result)

    ret = judge_llm.invoke(
        EVAL_PROMPT.format(
            starting_code=inputs["starting_code"],
            expectations=reference_outputs["expectations"],
            outputs=outputs,
        )
    )

    return EvaluatorResult(
        key="code_evaluation",
        score=ret["score"],
        comment=ret["comment"],
    )


async def evaluate_code(
    inputs: CodeEvaluatorInputs,
    outputs: str,
    reference_outputs: CodeEvaluatorReferenceOutputs,
) -> EvaluatorResult:
    return await _arun_evaluator(
        run_name="coder",
        scorer=evaluate_code_scorer,
        feedback_key="coder",
        inputs=inputs,
        outputs=outputs,
        reference_outputs=reference_outputs,
    )


@pytest.mark.asyncio
async def test_coder_creates_rest_api():
    mock_api = MockGithubApi()
    github_tools = get_github_tools(mock_api)

    # Create and build graph
    graph = graph_builder(github_tools).compile()

    input = "Create a python JSON REST API server with a root entry point"

    result = await graph.ainvoke(
        State(messages=[HumanMessage(content=input)]),
        config={
            "configurable": {"thread_id": str(uuid.uuid4())},
        },
    )

    starting_code = mock_api.files
    expectations = "The agent should have created a JSON REST API server with a '/hello' entry point. If it added dependencies, it should have added them to the proper dependencies file"

    eval_result = await evaluate_code(
        CodeEvaluatorInputs(starting_code=starting_code),
        result,
        CodeEvaluatorReferenceOutputs(expectations=expectations),
    )

    print(eval_result)
