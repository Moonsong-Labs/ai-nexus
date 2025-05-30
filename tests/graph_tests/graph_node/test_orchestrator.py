import pytest
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from testing.inputs import decode_base_messages

from orchestrator.graph import OrchestratorGraph
from orchestrator.state import State


@pytest.mark.asyncio
async def test_tool_call_none() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=[HumanMessage(content="Hi")],
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    actual_tool_calls = [t["name"] for t in getattr(last_message, "tool_calls", [])]

    assert [] == actual_tool_calls


@pytest.mark.asyncio
async def test_tool_call_requirements() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=[HumanMessage(content="I want to build a website")],
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    actual_tool_calls = [t["name"] for t in getattr(last_message, "tool_calls", [])]

    assert ["requirements"] == actual_tool_calls


@pytest.mark.asyncio
async def test_tool_call_architect() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=decode_base_messages(
                [
                    {
                        "content": "I want to build a website",
                        "role": "human",
                    },
                    {
                        "content": "I'll delegate this task to the Requirements Gatherer.",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "requirements",
                                "args": {"content": "website"},
                                "id": "1",
                            }
                        ],
                    },
                    {
                        "content": "MyWebsite is a personal blog intended for sharing personal experiences with friends and family.",
                        "role": "tool",
                        "name": "requirements",
                        "tool_call_id": "1",
                        "status": "success",
                    },
                ]
            ),
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    actual_tool_calls = [t["name"] for t in getattr(last_message, "tool_calls", [])]

    assert ["architect"] == actual_tool_calls


def normalize_whitespace(text: str) -> str:
    """Normalize text by removing extra whitespace and normalizing line endings."""
    if not isinstance(text, str):
        print(f"Expected string but got {type(text)}: {text}")
        text = str(text)
    return " ".join(text.split())


@pytest.mark.asyncio
async def test_tool_call_coder_with_full_task() -> None:
    orchestrator = OrchestratorGraph(
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )
    task_content = """id: 1\ntitle: Implement Fibonacci Iterator with Overflow Handling (Hobby Mode)\ndescription: |\n  **General Description:**\n  This task involves setting up the Rust project, implementing the core Fibonacci sequence iterator logic within a struct that implements the `Iterator` trait, and adding overflow handling for `u32` integers. It also includes creating a simple demonstration of the iterator's functionality and verifying it. This single task covers all essential requirements for this hobby project, excluding formal testing and CI/CD setup.\n\n  **High-Level Steps:**\n  1. Initialize a new Rust library project using Cargo.\n  2. Define a `Fibonacci` struct to hold the state of the sequence (e.g., two `u32` fields for the current and next Fibonacci numbers).\n  3. Implement a `new()` constructor for the `Fibonacci` struct to initialize the starting state (0 and 1).\n  4. Implement the `Iterator` trait for the `Fibonacci` struct.\n  5. Within the `next()` method of the `Iterator` trait, calculate the next Fibonacci number.\n  6. Implement logic to detect `u32` integer overflow before updating the state. If overflow occurs, return `None`. Otherwise, return `Some(value)` with the current Fibonacci number and update the state for the next iteration.\n  7. Create a simple example in `src/lib.rs` or a separate example file to demonstrate the iterator's usage, iterating through the sequence and printing values until overflow is reached.\n  8. Build the project using `cargo build`.\n  9. Run the example using `cargo run --example <example_name>` (if a separate example file is created) or verify functionality within a simple main function if implemented directly in `lib.rs`.\nstatus: pending\ndependencies: []\npriority: high\nissueLink: N/A\npullRequestLink:\nskillRequirements:\n  - Rust programming\n  - Cargo build tool\nacceptanceCriteria:\n  - A new Rust library project is initialized.\n  - The `Fibonacci` struct is defined with appropriate state fields.\n  - The `new()` constructor is implemented and correctly initializes the state.\n  - The `Iterator` trait is implemented for the `Fibonacci` struct.\n  - The `next()` method correctly calculates and yields Fibonacci numbers.\n  - The `next()` method correctly detects `u32` integer overflow and returns `None`.\n  - A working example demonstrates the iterator's functionality, including reaching the overflow point.\n  - The project builds successfully using Cargo.\n  - The example runs and produces the expected output, showing the sequence and the termination at overflow.\nestimatedHours: 6\ncontextualInformation: |\n  Purpose: Create a simple and efficient Fibonacci sequence iterator in Rust. It serves as a learning exercise and a demonstration of implementing iterators in Rust.\n  Functionality:\n  - The library should provide a struct that implements the `Iterator` trait.\n  - The iterator should yield the next Fibonacci number in the sequence.\n  - The iterator should handle integer overflows gracefully by returning `None` when an overflow occurs.\n  User Experience Goals:\n  - Easy to use and integrate into other Rust projects.\n  - Clear and concise API.\n  - Well-documented code.\ntechnicalRequirements: |\n  Technologies Used: Rust, Cargo.\n  Development Setup: Rust toolchain, Cargo.\n  Technical Constraints: Integer overflow needs to be handled for `u32`.\n  Dependencies: No external dependencies required.\n  Tool Usage Patterns: Cargo for building, testing, and managing.\nrelatedCodingContext: |\n  Recent changes: Basic Fibonacci iterator and overflow detection implemented.\n  Next steps: Write unit tests (skipped in Hobby mode), add documentation.\n  Active decisions and considerations: Choosing appropriate test cases (skipped in Hobby mode).\n  Important patterns and preferences: Using Rust's built-in testing framework (skipped in Hobby mode).\n  Learnings and project insights: Handling integer overflows.\nsystemPatternGuidance: |\n  Architecture: Single struct `Fibonacci` implementing `Iterator`. Holds current state.\n  Key Technical Decisions: Use `u32`, implement overflow detection, provide `new()` constructor.\n  Design Patterns: Iterator trait implementation.\n  Component Relationships: `Fibonacci` struct is self-contained.\n  Critical Implementation Paths: The `next()` method - calculate next number, detect overflows, return `Some(value)` or `None`.\ntestingRequirements: N/A - Hobby mode"""

    result = await orchestrator.compiled_graph.nodes["orchestrator"].ainvoke(
        State(
            messages=decode_base_messages(
                [
                    {
                        "content": "I want to build a library that implements a Fibonacci iterator in Rust",
                        "role": "human",
                    },
                    {
                        "content": "I'll delegate this task to the Requirements Gatherer.",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "requirements",
                                "args": {"content": "website"},
                                "id": "1",
                            }
                        ],
                    },
                    {
                        "content": """# Fibonacci iterator library in Rust Requirements\n\n## Project Overview\n\nThis is a smaller, hobby/personal project to create a Fibonacci iterator library in Rust.\n\n## Functional Requirements\n\n*   Core functionality: Fibonacci sequence iterator.\n*   Error Handling: Overflow returns None.""",
                        "role": "tool",
                        "name": "requirements",
                        "tool_call_id": "1",
                        "status": "success",
                    },
                    {
                        "content": "Okay, now that we have the requirements, let's move on to the architectural design.",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "architect",
                                "args": {
                                    "content": "Fibonacci iterator library in Rust"
                                },
                                "id": "2",
                            }
                        ],
                    },
                    {
                        "content": """The Fibonacci Iterator Library in Rust is designed as a hobby project to create a simple and efficient Fibonacci sequence iterator. The library consists of a single struct, `Fibonacci`, which implements the `Iterator` trait, using `u32` to represent Fibonacci numbers and handling integer overflows gracefully by returning `None`. The core implementation path is the `next()` method, which calculates the next Fibonacci number, detects overflows, and returns `Some(value)` or `None`. Technologies used include Rust and Cargo, with no external dependencies. The project is currently in the initial implementation phase, with comprehensive unit tests and documentation remaining to be built. This project is for hobby purposes.""",
                        "role": "tool",
                        "name": "architect",
                        "tool_call_id": "2",
                        "status": "success",
                    },
                    {
                        "content": "",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "task_manager",
                                "args": {
                                    "content": "Fibonacci iterator library in Rust"
                                },
                                "id": "3",
                            }
                        ],
                    },
                    {
                        "content": """Created a single task file (task-01-hobby-implementation.md) and a tasks.json file in the planning directory for the Fibonacci iterator library in Rust project. Operated in HOBBY mode, consolidating all core implementation, initialization, and demonstration requirements into one task and skipping testing and CI/CD setup as per HOBBY guidelines. A roadmap.md file was not created.""",
                        "role": "tool",
                        "name": "task_manager",
                        "tool_call_id": "3",
                        "status": "success",
                    },
                    {
                        "content": "",
                        "role": "ai",
                        "tool_calls": [
                            {
                                "name": "read_task_planning",
                                "args": {},
                                "id": "4",
                            }
                        ],
                    },
                    {
                        "content": task_content,
                        "role": "tool",
                        "name": "read_task_planning",
                        "tool_call_id": "4",
                        "status": "success",
                    },
                ]
            ),
        ),
        orchestrator.create_runnable_config({"configurable": {"thread_id": "1"}}),
        store=orchestrator.store,
    )

    last_message = result["messages"][-1]
    last_tool_call = last_message.tool_calls[0]
    print(f"Tool call content type: {type(last_tool_call['args']['content'])}")
    print(f"Task content type: {type(task_content)}")

    assert last_tool_call["name"] == "coder_new_pr"
    tool_content = str(last_tool_call["args"]["content"])
    task_content_str = str(task_content)
    assert normalize_whitespace(tool_content) == normalize_whitespace(task_content_str)
