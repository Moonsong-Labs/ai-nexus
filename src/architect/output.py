"""Missing docs."""

from typing import List

from pydantic import BaseModel, Field


class ArchitectAgentTaskOutput(BaseModel):
    """Missing docs."""

    id: str = Field(description="The unique identifier for the task")
    name: str = Field(description="Descriptive name of the task")
    description: str = Field(description="What the task accomplishes")
    task: str = Field(description="What the task accomplishes")
    requirement_id: str = Field(
        description="The unique identifier for the requirement that the task verifies"
    )


class ArchitectAgentQuestionOutput(BaseModel):
    """Missing docs."""

    id: str = Field(description="The unique identifier for the question")
    question: str = Field(description="The question to be answered")
    context: str = Field(description="The context for the question")


class ArchitectAgentFinalOutput(BaseModel):
    """Missing docs."""

    questions: List[ArchitectAgentQuestionOutput] = Field(
        description="A list of questions. May be empty if user already answered all questions."
    )
    tests: List[ArchitectAgentTaskOutput] = Field(
        description="A list of tests. May be empty if agent still has questions to ask."
    )
