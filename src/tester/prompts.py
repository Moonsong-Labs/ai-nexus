"""Define default prompts."""

with open("src/tester/test-agent-system-prompt.md", "r") as file:
    system_prompt_content = file.read()

if system_prompt_content is None:
  raise ValueError("test-agent-system-prompt.md is not found")

system_prompt_content = system_prompt_content.replace("{", "{{").replace("}", "}}")

SYSTEM_PROMPT = f"""
{system_prompt_content}

{{user_info}}

System Time: {{time}}"""

SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{user_info}}", "{user_info}")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{time}}", "{time}")

print(SYSTEM_PROMPT)
