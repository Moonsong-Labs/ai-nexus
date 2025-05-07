"""Missing docs."""

from typing import List

from pydantic import BaseModel, Field


class TesterAgentTestOutput(BaseModel):
    """Missing docs."""

    id: str = Field(description="The unique identifier for the test")
    name: str = Field(description="Descriptive name of the test")
    description: str = Field(description="What the test verifies")
    code: str = Field(description="Actual test code")
    requirement_id: str = Field(
        description="The unique identifier for the requirement that the test verifies"
    )


class TesterAgentQuestionOutput(BaseModel):
    """Missing docs."""

    id: str = Field(description="The unique identifier for the question")
    question: str = Field(description="The question to be answered")
    context: str = Field(description="The context for the question")


class TesterAgentFinalOutput(BaseModel):
    """Missing docs."""

    questions: List[TesterAgentQuestionOutput] = Field(
        description="A list of questions. May be empty if user already answered all questions."
    )
    tests: List[TesterAgentTestOutput] = Field(
        description="A list of tests. May be empty if agent still has questions to ask."
    )
