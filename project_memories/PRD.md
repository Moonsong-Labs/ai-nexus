# Goal

This project aims to create a fully functional team of AI agent to design, develop and maintain technical project.

# Technologies

## Core Technologies & Frameworks:

* Python: The primary programming language (version >= 3.12).
* LangGraph: Core framework for building the AI agents.
* LangChain: Foundational library for LLM application development.
* LangChain Google GenAI: Integration with Google's AI models (e.g., Gemini).

## Environment & Package Management:

* uv: Used for managing Python virtual environments and installing packages.
* python-dotenv: Manages environment variables from .env files.

## Development Workflow & Build:

* Make: Used as a task runner to automate common commands.
* setuptools / wheel: Standard Python tools for building packages.
* LangGraph CLI: Used for development tasks (langgraph dev).

## Testing & Code Quality:

* pytest: The main framework for running tests.
* pytest-asyncio: Enables testing of asynchronous code.
* pytest-dotenv: Loads environment variables specifically for tests.
* pytest-watch (ptw): Runs tests automatically when files change.
* ruff: Performs code linting and formatting.
* mypy: Conducts static type checking.
* codespell: Checks for spelling mistakes.
* openevals: Suggests involvement in evaluating language models.

## Version Control:

Git: Inferred from .gitignore and Makefile commands.

## LLM Models

* gemini-2.0-flash: Preferred model for simple task and quick evaluations
* gemini-2.5-pro-preview-03-25: Preferred model for complex tasks needing reasoning