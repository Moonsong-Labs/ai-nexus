"""Live updating orchestrator demo with Rich console output."""

import asyncio
import getpass
import json
import sys
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Literal, Optional
import time
from collections import deque

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

from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.rule import Rule

# Orchestrator imports - imported later to avoid initialization issues

console = Console()

class LiveMessageDisplay:
    """Live updating message display with Rich."""
    
    def __init__(self):
        self.console = Console()
        self.messages = deque(maxlen=10)  # Keep last 10 messages
        self.agent_stats = {}
        self.current_agent = None
        self.start_time = time.time()
        
        self.agent_colors = {
            "orchestrator": "bold magenta",
            "requirements": "bold cyan", 
            "architect": "bold blue",
            "task_manager": "bold green",
            "coder_new_pr": "bold yellow",
            "coder_change_request": "bold orange",
            "tester": "bold red",
            "code_reviewer": "bold purple",
            "tool": "dim white",
            "human": "bold white",
            "ai": "bold magenta",
            "system": "bold green",
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
            "system": "⚙️",
        }
    
    def create_layout(self) -> Layout:
        """Create the live display layout with responsive sizing."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),  # Responsive body takes remaining space
            Layout(name="footer", size=4)   # Compact footer
        )
        
        layout["body"].split_row(
            Layout(name="messages", ratio=3, minimum_size=40),  # 75% of width for messages
            Layout(name="stats", ratio=1, minimum_size=25)     # 25% of width for stats
        )
        
        return layout
    
    def render_header(self) -> Panel:
        """Render the header section."""
        elapsed = int(time.time() - self.start_time)
        minutes, seconds = divmod(elapsed, 60)
        
        header_text = Text.assemble(
            ("AI Nexus Orchestrator", "bold white on blue"),
            " | ",
            ("Live View", "bold green"),
            " | ",
            (f"Runtime: {minutes:02d}:{seconds:02d}", "dim white")
        )
        
        return Panel(
            Align.center(header_text, vertical="middle"),
            box=box.DOUBLE,
            style="blue"
        )
    
    def render_messages(self) -> Panel:
        """Render the messages section with responsive scrolling."""
        # Create message content without fixed dimensions
        content_lines = []
        
        if not self.messages:
            content_lines.append("Waiting for messages...")
        else:
            # Show last 10 messages to prevent excessive scrolling
            recent_messages = list(self.messages)[-10:]
            
            for msg_data in recent_messages:
                agent = msg_data["agent"]
                content = msg_data["content"]
                timestamp = msg_data["timestamp"]
                
                icon = self.agent_icons.get(agent, "📨")
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                
                # Create message header
                header = f"{icon} {agent.replace('_', ' ').title()} [{time_str}]"
                content_lines.append(header)
                
                # Add indented content (let Rich handle wrapping)
                if content.strip():
                    content_lines.append(f"  {content.strip()}")
                
                # Add separator
                content_lines.append("")
        
        # Create content text
        content_text = Text("\n".join(content_lines))
        
        # Calculate title
        total_messages = len(self.messages)
        if total_messages > 10:
            title = f"📨 Messages (showing last 10 of {total_messages})"
        else:
            title = f"📨 Messages ({total_messages} total)"
        
        return Panel(
            content_text,
            title=title,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1)
            # Removed fixed height and width for responsive sizing
        )
    
    def render_stats(self) -> Panel:
        """Render the statistics section with responsive sizing."""
        from rich.table import Table
        
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("Agent", style="white", no_wrap=True)
        table.add_column("Count", style="yellow", justify="right")
        table.add_column("Active", style="green", justify="center")
        
        # Show all agents or limit if too many
        sorted_agents = sorted(self.agent_stats.items(), key=lambda x: x[1], reverse=True)
        
        for agent, count in sorted_agents:
            icon = self.agent_icons.get(agent, "📨")
            is_active = "✓" if agent == self.current_agent else ""
            agent_name = agent.replace('_', ' ').title()
            
            table.add_row(
                f"{icon} {agent_name}",
                str(count),
                is_active
            )
        
        # If no agents yet, show placeholder
        if not sorted_agents:
            table.add_row("No activity yet", "", "")
        
        return Panel(
            table,
            title="📊 Agent Activity",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 1)
            # Removed fixed height and width for responsive sizing
        )
    
    def render_footer(self) -> Panel:
        """Render the footer with current activity."""
        if self.current_agent:
            icon = self.agent_icons.get(self.current_agent, "📨")
            color = self.agent_colors.get(self.current_agent, "white")
            
            activity_text = Text()
            activity_text.append(f"{icon} ", style=color)
            activity_text.append(f"{self.current_agent.replace('_', ' ').title()} ", style=f"bold {color}")
            activity_text.append("is working", style="dim white")
            
            # Add animated dots
            dots = "." * (int(time.time() * 3) % 4)
            activity_text.append(dots, style="bold white")
        else:
            activity_text = Text("💤 System Idle", style="dim green")
        
        return Panel(
            Align.center(activity_text, vertical="middle"),
            title="⚡ Status",
            border_style="yellow",
            box=box.ROUNDED,
            padding=(0, 1)
            # Removed fixed height for responsive sizing
        )
    
    def update_display(self, layout: Layout):
        """Update all sections of the display."""
        layout["header"].update(self.render_header())
        layout["messages"].update(self.render_messages())
        layout["stats"].update(self.render_stats())
        layout["footer"].update(self.render_footer())
    
    def add_message(self, agent: str, content: str):
        """Add a new message to the display."""
        self.messages.append({
            "agent": agent,
            "content": content.strip(),
            "timestamp": time.time()
        })
        
        # Update stats
        if agent not in self.agent_stats:
            self.agent_stats[agent] = 0
        self.agent_stats[agent] += 1
        
        self.current_agent = agent
    
    def process_messages_live(self, messages: list[dict]):
        """Process messages with live updates."""
        layout = self.create_layout()
        
        with Live(layout, refresh_per_second=4, console=self.console) as live:
            # Initial update
            self.update_display(layout)
            time.sleep(1)
            
            # Process each message
            next_tool_name = None
            for i, msg in enumerate(messages):
                msg_type = msg.get("type", "unknown")
                content = msg.get("content", "").strip()
                
                # Handle tool messages
                if msg_type == "tool" and next_tool_name:
                    msg_type = next_tool_name
                    next_tool_name = None
                elif msg_type == "ai":
                    msg_type = "orchestrator"
                
                # Check for tool calls
                if "tool_calls" in msg:
                    for tool_call in msg.get("tool_calls", []):
                        next_tool_name = tool_call.get("name", "tool")
                        tool_content = tool_call.get("args", {}).get("content", str(tool_call.get("args", {})))
                        if tool_content:
                            self.add_message(next_tool_name, tool_content[:200])
                            self.update_display(layout)
                            time.sleep(0.5)  # Simulate processing
                
                # Add main message
                if content:
                    self.add_message(msg_type, content)
                    self.update_display(layout)
                    time.sleep(0.8)  # Simulate thinking time
            
            # Final state
            self.current_agent = None
            self.update_display(layout)
            time.sleep(2)


def print_messages_live(messages: list[dict]):
    """Display messages with live updates."""
    display = LiveMessageDisplay()
    display.process_messages_live(messages)
    
    # Show final summary
    console.print("\n")
    console.rule("[bold cyan]Session Complete[/bold cyan]")
    console.print(f"\n[bold green]✓[/] Processed {len(messages)} messages")
    console.print(f"[bold blue]ℹ[/] Involved {len(display.agent_stats)} different agents")
    console.print("\n")


if __name__ == "__main__":
    # Import orchestrator components here to avoid initialization issues
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
    
    args = sys.argv[1:]
    human_or_ai: Literal["human", "ai"] = "ai"

    if len(args) >= 1:
        if args[0] in ["human", "ai"]:
            human_or_ai = args[0]
        else:
            console.print(f"[bold red]Error:[/] Unknown mode: {args[0]}, (need: human|ai)")
            exit(1)
    
    display = LiveMessageDisplay()
    use_human_ai = human_or_ai == "ai"
    
    # Configuration section - THIS IS WHERE YOU SET WHICH AGENTS ARE STUBS!
    orchestrator = OrchestratorGraph(
        agent_config=OrchestratorConfiguration(
            requirements_agent=RequirementsAgentConfig(
                use_stub=False,  # Set to True to use stub
                config=RequirementsConfiguration(use_human_ai=use_human_ai),
            ),
            architect_agent=ArchitectAgentConfig(
                use_stub=False,  # Set to True to use stub
            ),
            task_manager_agent=TaskManagerAgentConfig(
                use_stub=False,  # Set to True to use stub
                config=TaskManagerConfiguration(),
            ),
            tester_agent=TesterAgentConfig(
                use_stub=False,  # Set to True to use stub
                config=TesterConfiguration(),
            ),
            coder_new_pr_agent=SubAgentConfig(
                use_stub=False,  # Set to True to use stub
            ),
            coder_change_request_agent=SubAgentConfig(
                use_stub=True,  # This one is set as stub
            ),
            reviewer_agent=CodeReviewerAgentConfig(
                use_stub=False,  # Set to True to use stub
            ),
        ),
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )

    run_id = str(uuid.uuid4())
    user = getpass.getuser()

    # Start live display
    layout = display.create_layout()
    
    @traceable(
        run_type="chain",
        name="Orchestrator Demo",
        tags=["demo", f"user:{user}"],
    )
    async def _exec():
        """
        Executes the orchestrator with real-time display updates.
        """
        config = orchestrator.create_runnable_config(
            RunnableConfig(
                recursion_limit=250,
                configurable={
                    "thread_id": str(uuid.uuid4()),
                },
            )
        )
        
        # Track the last tool name for proper message attribution
        last_tool_name = None
        
        # Use regular astream for simpler, more reliable streaming
        async for chunk in orchestrator.compiled_graph.astream(
            State(
                messages=HumanMessage(
                    content="I want to build a python stack data structure"
                )
            ),
            config=config
        ):
            # chunk is a dict with node_name: state_update
            for node_name, state_update in chunk.items():
                if "messages" in state_update and state_update["messages"]:
                    # Get the last message from this node
                    new_messages = state_update["messages"]
                    if isinstance(new_messages, list) and new_messages:
                        last_message = new_messages[-1]
                        
                        # Determine agent name from node or message type
                        agent_name = node_name
                        if hasattr(last_message, "name") and last_message.name:
                            agent_name = last_message.name
                        elif node_name == "__start__":
                            agent_name = "human"
                        elif "orchestrator" in node_name.lower():
                            agent_name = "orchestrator"
                        
                        # Clean up agent name
                        agent_name = agent_name.lower().replace(" ", "_").replace("_agent", "")
                        
                        # Update current agent
                        if agent_name in display.agent_colors:
                            display.current_agent = agent_name
                        
                        # Add message content
                        content = ""
                        if hasattr(last_message, "content"):
                            content = last_message.content
                        elif hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            # Handle tool calls
                            for tool_call in last_message.tool_calls:
                                tool_name = tool_call.get("name", "")
                                if tool_name in ["requirements", "architect", "task_manager", 
                                               "coder_new_pr", "coder_change_request", 
                                               "tester", "code_reviewer"]:
                                    tool_args = tool_call.get("args", {})
                                    if "content" in tool_args:
                                        display.add_message(tool_name, f"Calling: {tool_args['content']}")
                                        display.update_display(layout)
                        
                        if content:
                            display.add_message(agent_name, content)
                            display.update_display(layout)

        # Handle any interrupts after streaming
        while True:
            graph_state = await orchestrator.compiled_graph.aget_state(config)
            if graph_state.interrupts:
                interrupt = graph_state.interrupts[0]
                
                # Temporarily exit live display for input
                display.current_agent = "requirements"
                display.add_message("requirements", interrupt.value['query'])
                display.update_display(layout)
                
                # Show interrupt panel below the live display
                interrupt_panel = Panel(
                    Text(interrupt.value['query'], style="bold cyan"),
                    title="❓ Requirements Query",
                    title_align="left",
                    border_style="cyan",
                    box=box.HEAVY,
                    padding=(1, 2),
                    expand=True
                )
                
                # We need to handle this within the Live context
                # For now, we'll need to pause the live display
                response = input("\n\nYour Answer: ")
                
                display.add_message("human", response)
                display.update_display(layout)
                
                # Resume with the response using astream
                async for chunk in orchestrator.compiled_graph.astream(
                    Command(resume=response),
                    config=config
                ):
                    # Process chunk same as above
                    for node_name, state_update in chunk.items():
                        if "messages" in state_update and state_update["messages"]:
                            new_messages = state_update["messages"]
                            if isinstance(new_messages, list) and new_messages:
                                last_message = new_messages[-1]
                                agent_name = node_name.lower().replace(" ", "_").replace("_agent", "")
                                
                                if hasattr(last_message, "content") and last_message.content:
                                    display.add_message(agent_name, last_message.content)
                                    display.update_display(layout)
            else:
                break
                
        # Mark as complete
        display.current_agent = None
        display.update_display(layout)
        
        return {"status": "complete"}

    organization_id = "265bce82-15be-4d5e-9ae9-55d5e7b4e96e"
    project_id = "a6835858-9241-4360-9c88-44d5fe9ca98e"
    trace_url = f"https://smith.langchain.com/o/{organization_id}/projects/p/{project_id}/r/{run_id}?traceId={run_id}&mode=graph"
    
    # Display trace link with Rich formatting
    trace_panel = Panel(
        Text.assemble(
            ("Trace: ", "bold white"),
            (trace_url, "bold magenta underline")
        ),
        box=box.DOUBLE_EDGE,
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(trace_panel)
    console.print("")
    
    # Initialize display
    display.add_message("system", "Starting AI Nexus Orchestrator...")
    display.update_display(layout)
    
    # Run with live display
    with Live(layout, refresh_per_second=4, console=console, screen=True) as live:
        display.update_display(layout)
        
        # Add a startup message
        display.add_message("system", "Initializing orchestrator graph...")
        display.update_display(layout)
        time.sleep(1)
        
        # Start the execution
        try:
            result = asyncio.run(_exec(langsmith_extra={"run_id": run_id}))
            
            # Show completion
            display.add_message("system", "Orchestration completed successfully!")
            display.current_agent = None
            display.update_display(layout)
            time.sleep(3)
        except Exception as e:
            display.add_message("system", f"Error: {str(e)}")
            display.update_display(layout)
            time.sleep(3)
    
    # Final summary
    console.print("\n")
    console.rule("[bold cyan]Session Complete[/bold cyan]")
    console.print(f"\n[bold green]✓[/] Processed {len(display.messages)} messages")
    console.print(f"[bold blue]ℹ[/] Involved {len(display.agent_stats)} different agents")
    console.print("\n")