"""Enhanced orchestrator demo with Rich console output."""

import asyncio
import getpass
import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Literal, Optional
import time

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from langsmith import RunTree, traceable
from langsmith.client import Client
from langsmith.evaluation import EvaluationResult
from pydantic import BaseModel

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box
from rich.align import Align
from rich.padding import Padding

# Only import these for exec mode
if "exec" in sys.argv:
    from orchestrator.configuration import (
        ArchitectAgentConfig,
        CodeReviewerAgentConfig,
        RequirementsAgentConfig,
        RequirementsConfiguration,
        SubAgentConfig,
        TaskManagerAgentConfig,
        TaskManagerConfiguration,
        TesterAgentConfig,
        TesterConfiguration,
    )
    from orchestrator.configuration import (
        Configuration as OrchestratorConfiguration,
    )
    from orchestrator.graph import OrchestratorGraph
    from orchestrator.state import State

OUTPUT_DUMP_FILE = "dump.json"

console = Console()

class MessageDisplay:
    """Enhanced message display with Rich formatting."""
    
    def __init__(self):
        self.console = Console()
        self.agent_colors = {
            "orchestrator": "bold magenta",
            "requirements": "bold cyan",
            "architect": "bold blue",
            "task_manager": "bold green",
            "coder_new_pr": "bold yellow",
            "coder_change_request": "bold yellow",
            "tester": "bold red",
            "code_reviewer": "bold purple",
            "tool": "dim white",
            "human": "bold white",
            "ai": "bold magenta",
        }
        self.agent_icons = {
            "orchestrator": "🎭",
            "requirements": "📋",
            "architect": "🏗️",
            "task_manager": "📊",
            "coder_new_pr": "💻",
            "coder_change_request": "✏️",
            "tester": "🧪",
            "code_reviewer": "🔍",
            "tool": "🔧",
            "human": "👤",
            "ai": "🤖",
        }
        
    def format_content(self, content: str, max_length: int = 80) -> str:
        """Format content with proper line wrapping."""
        if len(content) <= max_length:
            return content
        
        words = content.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(" ".join(current_line))
            
        return "\n".join(lines)
    
    def create_message_panel(self, agent_type: str, content: str, tool_calls: Optional[list] = None) -> Panel:
        """Create a rich panel for a message."""
        icon = self.agent_icons.get(agent_type, "📨")
        color = self.agent_colors.get(agent_type, "white")
        
        formatted_content = self.format_content(content)
        
        # Create the main text
        text = Text(formatted_content, style="white")
        
        # Add tool calls if present
        if tool_calls:
            text.append("\n\n", style="white")
            for tool_call in tool_calls:
                tool_name = tool_call.get('name', 'unknown')
                tool_icon = self.agent_icons.get(tool_name, "🔧")
                tool_color = self.agent_colors.get(tool_name, "dim cyan")
                
                text.append(f"  {tool_icon} ", style=tool_color)
                text.append(f"{tool_name}", style=f"bold {tool_color}")
                
                if tool_name in ["requirements", "architect", "task_manager", "coder_new_pr", 
                               "coder_change_request", "tester", "code_reviewer"]:
                    args_content = tool_call.get('args', {}).get('content', '')
                    if args_content:
                        formatted_args = self.format_content(args_content, max_length=60)
                        text.append(f"\n     └─ ", style="dim white")
                        text.append(formatted_args, style="dim white")
                else:
                    args = tool_call.get('args', {})
                    if args:
                        text.append(f"\n     └─ ", style="dim white")
                        text.append(str(args), style="dim white")
                text.append("\n", style="white")
        
        # Create panel with agent name as title
        panel = Panel(
            text,
            title=f"{icon} {agent_type.replace('_', ' ').title()}",
            title_align="left",
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 2),
            expand=True
        )
        
        return panel
    
    def display_message_with_animation(self, msg: dict):
        """Display a message with typing animation."""
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", "").strip()
        tool_calls = msg.get("tool_calls", None)
        
        # Map message types to agent types
        if msg_type == "ai":
            msg_type = "orchestrator"
        elif msg_type == "tool" and hasattr(self, '_next_tool_name'):
            msg_type = self._next_tool_name
            delattr(self, '_next_tool_name')
        
        # Store next tool name if present
        if tool_calls:
            for tool_call in tool_calls:
                self._next_tool_name = tool_call.get('name', 'tool')
                break
        
        # Skip empty messages
        if not content and not tool_calls:
            return
        
        # Create the panel
        panel = self.create_message_panel(msg_type, content, tool_calls)
        
        # Display with fade-in effect
        with self.console.status(f"[{self.agent_colors.get(msg_type, 'white')}]Processing...", spinner="dots"):
            time.sleep(0.3)  # Simulate processing
        
        self.console.print(panel)
        self.console.print("")  # Add spacing
    
    def display_messages(self, messages: list[dict]):
        """Display all messages with animations."""
        self.console.clear()
        
        # Header
        header = Panel(
            Align.center(
                Text("AI Nexus Orchestrator", style="bold white on blue"),
                vertical="middle"
            ),
            box=box.DOUBLE,
            style="bold blue",
            padding=(1, 2),
            expand=True
        )
        self.console.print(header)
        self.console.print("")
        
        # Process messages
        for msg in messages:
            self.display_message_with_animation(msg)
    
    def display_trace_link(self, trace_url: str):
        """Display the trace link in a fancy panel."""
        trace_panel = Panel(
            Align.center(
                Text(trace_url, style="bold magenta underline"),
                vertical="middle"
            ),
            title="🔗 Trace Link",
            title_align="center",
            border_style="magenta",
            box=box.DOUBLE_EDGE,
            padding=(1, 2),
            expand=True
        )
        self.console.print(trace_panel)
        self.console.print("")
    
    def display_interrupt(self, query: str) -> str:
        """Display an interrupt query and get user input."""
        interrupt_panel = Panel(
            Text(query, style="bold cyan"),
            title="❓ Requirements Query",
            title_align="left",
            border_style="cyan",
            box=box.HEAVY,
            padding=(1, 2),
            expand=True
        )
        
        self.console.print(interrupt_panel)
        response = self.console.input("[bold yellow]Your Answer:[/] ")
        self.console.print("")
        return response
    
    def display_summary_table(self, messages: list[dict]):
        """Display a summary table of all agents involved."""
        agent_counts = {}
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            if msg_type == "ai":
                msg_type = "orchestrator"
            
            if msg_type not in agent_counts:
                agent_counts[msg_type] = 0
            agent_counts[msg_type] += 1
        
        table = Table(title="Session Summary", box=box.ROUNDED, title_style="bold white")
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Messages", style="magenta")
        table.add_column("Icon", style="white")
        
        for agent, count in sorted(agent_counts.items()):
            icon = self.agent_icons.get(agent, "📨")
            table.add_row(
                agent.replace('_', ' ').title(),
                str(count),
                icon
            )
        
        self.console.print(table)


def print_messages_rich(messages: list[dict]):
    """Enhanced message printing with Rich library."""
    display = MessageDisplay()
    display.display_messages(messages)
    display.display_summary_table(messages)


if __name__ == "__main__":
    args = sys.argv[1:]
    mode: Literal["exec", "read"] = "read"
    human_or_ai: Literal["human", "ai"] = "human"

    if len(args) < 1:
        console.print("[bold red]Error:[/] Need an argument: exec|read")
        exit(1)
    else:
        mode = args[0]
        if mode == "exec":
            if len(args) < 2:
                console.print("[bold red]Error:[/] Need an argument: human|ai")
                exit(1)
            else:
                human_or_ai = args[1]

    if mode == "exec":
        display = MessageDisplay()
        use_human_ai = human_or_ai == "ai"
        
        # Show initialization
        with console.status("[bold green]Initializing orchestrator...", spinner="dots2"):
            orchestrator = OrchestratorGraph(
                agent_config=OrchestratorConfiguration(
                    requirements_agent=RequirementsAgentConfig(
                        use_stub=False,
                        config=RequirementsConfiguration(use_human_ai=use_human_ai),
                    ),
                    architect_agent=ArchitectAgentConfig(
                        use_stub=False,
                    ),
                    task_manager_agent=TaskManagerAgentConfig(
                        use_stub=False,
                        config=TaskManagerConfiguration(),
                    ),
                    tester_agent=TesterAgentConfig(
                        use_stub=False,
                        config=TesterConfiguration(),
                    ),
                    coder_new_pr_agent=SubAgentConfig(
                        use_stub=False,
                    ),
                    coder_change_request_agent=SubAgentConfig(
                        use_stub=True,
                    ),
                    reviewer_agent=CodeReviewerAgentConfig(
                        use_stub=False,
                    ),
                ),
                checkpointer=InMemorySaver(),
                store=InMemoryStore(),
            )
            time.sleep(1)  # Dramatic effect

        run_id = str(uuid.uuid4())
        user = getpass.getuser()

        @traceable(
            run_type="chain",
            name="Orchestrator Demo",
            tags=["demo", f"user:{user}"],
        )
        async def _exec():
            config = orchestrator.create_runnable_config(
                RunnableConfig(
                    recursion_limit=250,
                    configurable={
                        "thread_id": str(uuid.uuid4()),
                    },
                )
            )
            
            # Show starting message
            start_panel = Panel(
                Align.center(
                    Text("Starting orchestration...\n\nRequest: I want to build a python stack data structure", 
                         style="bold white"),
                    vertical="middle"
                ),
                border_style="green",
                box=box.DOUBLE,
                padding=(2, 4),
                expand=True
            )
            console.print(start_panel)
            console.print("")
            
            result = await orchestrator.compiled_graph.ainvoke(
                State(
                    messages=HumanMessage(
                        content="I want to build a python stack data structure"
                    )
                ),
                config=config,
            )

            # Handle interrupts
            while True:
                graph_state = await orchestrator.compiled_graph.aget_state(config)
                if graph_state.interrupts:
                    interrupt = graph_state.interrupts[0]
                    response = display.display_interrupt(interrupt.value['query'])
                    result = await orchestrator.compiled_graph.ainvoke(
                        Command(resume=response), config=config
                    )
                else:
                    break

            return result

        organization_id = "265bce82-15be-4d5e-9ae9-55d5e7b4e96e"
        project_id = "a6835858-9241-4360-9c88-44d5fe9ca98e"
        trace_url = f"https://smith.langchain.com/o/{organization_id}/projects/p/{project_id}/r/{run_id}?traceId={run_id}&mode=graph"
        
        display.display_trace_link(trace_url)

        result = asyncio.run(_exec(langsmith_extra={"run_id": run_id}))

        class _CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                elif isinstance(obj, datetime):
                    return obj.isoformat()
                elif hasattr(obj, "__dataclass_fields__"):
                    return asdict(obj)
                elif isinstance(obj, RunTree):
                    return obj.dict()
                elif isinstance(obj, BaseMessage):
                    return obj.model_dump()
                elif isinstance(obj, BaseModel):
                    return obj.model_dump()
                elif isinstance(obj, EvaluationResult):
                    return obj.dict()
                elif isinstance(obj, Client):
                    return {
                        "api_url": obj.api_url,
                        "tenant_id": str(obj._tenant_id)
                        if hasattr(obj, "_tenant_id")
                        else None,
                    }
                return super().default(obj)

        result_json = json.dumps(result, cls=_CustomEncoder)
        with open(OUTPUT_DUMP_FILE, "w") as f:
            f.write(result_json)

        print_messages_rich(json.loads(result_json)["messages"])
        
    elif mode == "read":
        with open(OUTPUT_DUMP_FILE) as f:
            result = json.load(f)
            print_messages_rich(result["messages"])
    else:
        console.print(f"[bold red]Error:[/] Invalid mode: {mode}, allowed exec|read")