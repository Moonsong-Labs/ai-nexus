"""Define default prompts."""

### System prompt
with open("src/code_reviewer/system_prompt.md", "r") as file:
    system_prompt_content = file.read()

if system_prompt_content is None:
  raise ValueError("File prompt is not found")

SYSTEM_PROMPT = f"""
{system_prompt_content}
{{user_info}}
System Time: {{time}}"""

SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{user_info}}", "{user_info}")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{time}}", "{time}")

### Question prompt (used for evaluation testing
with open("src/code_reviewer/question_prompt.md", "r") as file:
    question_prompt_content = file.read()

if question_prompt_content is None:
  raise ValueError("File prompt is not found")

QUESTION_PROMPT = f"""
{question_prompt_content}
System Time: {{time}}"""

QUESTION_PROMPT = QUESTION_PROMPT.replace("{{user_info}}", "{user_info}")
QUESTION_PROMPT = QUESTION_PROMPT.replace("{{time}}", "{time}")