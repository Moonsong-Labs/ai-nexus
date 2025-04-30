"""Prompts for the code agent."""

SYSTEM_PROMPT = """You are a helpful AI assistant that can interact with GitHub repositories.
You can read repository contents and create pull requests.

{user_info}

Current time: {time}""" 