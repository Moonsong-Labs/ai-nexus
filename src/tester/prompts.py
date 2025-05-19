"""Define default prompts."""

import logging

logger = logging.getLogger(__name__)

with open("src/tester/test-agent-system-prompt.md") as file:
    system_prompt_content = file.read()

with open("src/tester/test-agent-testing-workflow-stage.md") as file:
    testing_content = file.read()

if system_prompt_content is None or not system_prompt_content.strip():
    raise ValueError("test-agent-system-prompt.md is empty or not found")

if testing_content is None or not testing_content.strip():
    raise ValueError("test-agent-testing-workflow-stage.md is empty or not found")

system_prompt_content = system_prompt_content.replace("{", "{{").replace("}", "}}")
testing_content = testing_content.replace("{", "{{").replace("}", "}}")

# Map workflow stages to their content
WORKFLOW_STAGE_PROMPTS = {
    "testing": testing_content,
}

SYSTEM_PROMPT = f"""
{system_prompt_content}

{{workflow_stage}}

{{user_info}}

System Time: {{time}}"""

SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{user_info}}", "{user_info}")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{time}}", "{time}")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{workflow_stage}}", "{workflow_stage}")


def get_stage_prompt(stage_name):
    """Get the prompt for a specific workflow stage.

    Args:
        stage_name: The name of the workflow stage

    Returns:
        The prompt for the specified stage
    """
    prompt = WORKFLOW_STAGE_PROMPTS.get(stage_name, "")
    if not prompt:
        logger.warning(f"No prompt found for workflow stage: {stage_name}")
    return prompt
