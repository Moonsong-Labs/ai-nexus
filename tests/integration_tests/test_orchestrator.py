import uuid

import pytest
from agentevals.trajectory.llm import create_trajectory_llm_as_judge
from langchain_core.messages import HumanMessage
from termcolor import colored

from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State

CUSTOM_TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE = """You are an expert data labeler.
Your task is to grade the accuracy of an AI agent's internal trajectory when developing a software project.

<Rubric>
  An accurate trajectory:
  - Makes logical sense between steps
  - Shows clear progression
  - Is relatively efficient, though it does not need to be perfectly efficient
  - Is semantically equivalent to the provided reference trajectory
</Rubric>

Based on the following reference trajectory:

<reference_trajectory>
{reference_outputs}
</reference_trajectory>

Grade this actual trajectory:

<trajectory>
{outputs}
</trajectory>
"""


@pytest.mark.asyncio
async def test_orchestrator(pytestconfig):
    reference_outputs = [
        {"role": "human", "content": "I want to build a project"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "Delegate",
                        "arguments": '{"to": "requirements"}',
                    }
                }
            ],
        },
        {"role": "tool", "content": "I collected all requirements."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "Delegate",
                        "arguments": '{"to": "architect"}',
                    }
                }
            ],
        },
        {"role": "tool", "content": "I finished designing."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "Delegate",
                        "arguments": '{"to": "coder_new_pr"}',
                    }
                }
            ],
        },
        {"role": "tool", "content": "I finished coding."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "memorize",
                        "arguments": '{"origin": "requirements", "content": "Memorize something"}',
                    }
                }
            ],
        },
        {"role": "tool", "content": "I have memorized."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "Delegate",
                        "arguments": '{"to": "tester"}',
                    }
                }
            ],
        },
        {"role": "tool", "content": "I finished testing."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "Delegate",
                        "arguments": '{"to": "code_reviewer"}',
                    }
                }
            ],
        },
        {"role": "tool", "content": "I finished reviewing."},
        {"role": "assistant", "content": "The project is done."},
    ]

    graph = OrchestratorGraph().compiled_graph
    result = await graph.ainvoke(
        State(
            messages=[HumanMessage(content="I want to build a website to sell plants")]
        ),
        config={
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 100,
        },
    )

    evaluator = create_trajectory_llm_as_judge(
        prompt=CUSTOM_TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
        model="google_genai:gemini-2.0-flash-lite",
        continuous=True,
    )
    eval_result = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_outputs,
    )

    print()
    print("=" * 16)
    print(f"∥ score: {colored(f'{eval_result["score"]:.2f}', 'green')}  ∥")
    print("=" * 16)
    print(f"{colored(eval_result['comment'], 'cyan')}\n")
