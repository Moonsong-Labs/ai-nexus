"""Define default prompts."""

with open("src/code_reviewer/system_prompt.md") as file:
    system_prompt_content = file.read()

if system_prompt_content is None:
    raise ValueError("File prompt is not found")

SYSTEM_PROMPT = f"""
{system_prompt_content}
{{user_info}}
System Time: {{time}}"""

SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{user_info}}", "{user_info}")
SYSTEM_PROMPT = SYSTEM_PROMPT.replace("{{time}}", "{time}")

# Prompt for PR reviews
PR_REVIEW_PROMPT = """
Your task is to review a pull request (PR) and provide feedback. You will receive a diff of the PR,
which includes the changes made to the code. Using the GitHub tools, you should pull all the files
from the PR, read them, and then consider the diff. When it makes sense, feedback should be given
on the diff itself. You should also provide a summary of the feedback in the PR. The feedback
should be constructive and helpful. Use GitHub Markdown for formatting in your response.
"""

# Prompt for local code reviews
LOCAL_REVIEW_PROMPT = """

Project Path: {project_path}

Your task is to review the code on local disk and provide feedback. You should describe any
suggested changes with respect to the files in the directory. You should also provide a summary
of the feedback, and make it clear whether or not you approve the changes.

You will be given the path of the project as `project_path`. Read all relevant files needed to
understand the codebase, judging by their file extension.

Always summarize your work for debug purposes at the end and call the summarize tool.
"""
