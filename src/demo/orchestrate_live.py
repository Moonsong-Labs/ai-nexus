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
        """Create the live display layout with fixed sizes."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", size=20),  # Fixed height for body
            Layout(name="footer", size=6)   # Reduced footer size
        )
        
        layout["body"].split_row(
            Layout(name="messages", ratio=3, minimum_size=40),  # Minimum width for messages
            Layout(name="stats", ratio=1, minimum_size=20)     # Minimum width for stats
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
        """Render the messages section with scrollbar and fixed dimensions."""
        from rich.console import Group
        from rich.text import Text
        from rich.table import Table
        from rich.columns import Columns
        
        # Fixed viewport dimensions
        viewport_height = 12  # Lines available for content (16 - 4 for borders/padding)
        viewport_width = 55   # Characters available for content
        
        # Prepare all message lines
        all_lines = []
        
        if not self.messages:
            all_lines = ["Waiting for messages..."]
        else:
            for msg_data in self.messages:
                agent = msg_data["agent"]
                content = msg_data["content"]
                timestamp = msg_data["timestamp"]
                
                icon = self.agent_icons.get(agent, "📨")
                color = self.agent_colors.get(agent, "white")
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                
                # Create message header line
                header_line = f"{icon} {agent.replace('_', ' ').title()} [{time_str}]"
                all_lines.append(header_line)
                
                # Wrap content to exact width
                words = content.split()
                current_line = []
                current_length = 0
                
                for word in words:
                    if current_length + len(word) + 1 <= viewport_width:
                        current_line.append(word)
                        current_length += len(word) + 1
                    else:
                        if current_line:
                            all_lines.append("  " + " ".join(current_line))
                        current_line = [word]
                        current_length = len(word) + 2  # +2 for indentation
                
                if current_line:
                    all_lines.append("  " + " ".join(current_line))
                
                # Add separator line
                all_lines.append("")
        
        # Calculate scroll position (show last viewport_height lines)
        total_lines = len(all_lines)
        start_idx = max(0, total_lines - viewport_height)
        visible_lines = all_lines[start_idx:start_idx + viewport_height]
        
        # Pad to exact height to prevent border flickering
        while len(visible_lines) < viewport_height:
            visible_lines.append("")
        
        # Create scroll bar
        scroll_bar = []
        if total_lines > viewport_height:
            scroll_ratio = start_idx / max(1, total_lines - viewport_height)
            for i in range(viewport_height):
                line_ratio = i / viewport_height
                if abs(line_ratio - scroll_ratio) < 0.1:
                    scroll_bar.append("█")
                elif total_lines > viewport_height:
                    scroll_bar.append("│")
                else:
                    scroll_bar.append(" ")
        else:
            scroll_bar = [" "] * viewport_height
        
        # Create content with fixed width
        content_lines = []
        for i, line in enumerate(visible_lines):
            # Ensure each line is exactly the right width
            if len(line) > viewport_width:
                line = line[:viewport_width-3] + "..."
            else:
                line = line.ljust(viewport_width)
            
            # Add scroll bar
            content_lines.append(f"{line} {scroll_bar[i] if i < len(scroll_bar) else ' '}")
        
        # Create fixed content
        content_text = Text("\n".join(content_lines))
        
        # Show scroll info in title
        if total_lines > viewport_height:
            showing_start = start_idx + 1
            showing_end = min(start_idx + viewport_height, total_lines)
            title = f"📨 Messages ({showing_start}-{showing_end} of {total_lines})"
        else:
            title = f"📨 Messages ({total_lines} total)"
        
        return Panel(
            content_text,
            title=title,
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 1),
            height=16,  # Absolutely fixed height
            width=65    # Absolutely fixed width
        )
    
    def render_stats(self) -> Panel:
        """Render the statistics section with fixed dimensions."""
        from rich.table import Table
        
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        table.add_column("Agent", style="white", width=14)
        table.add_column("Count", style="yellow", justify="right", width=5)
        table.add_column("Active", style="green", justify="center", width=6)
        
        # Limit to exactly 10 rows to prevent overflow
        sorted_agents = sorted(self.agent_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        rows_added = 0
        for agent, count in sorted_agents:
            if rows_added >= 10:
                break
                
            icon = self.agent_icons.get(agent, "📨")
            is_active = "✓" if agent == self.current_agent else ""
            agent_name = agent.replace('_', ' ').title()
            
            # Truncate long agent names to fit exactly
            if len(agent_name) > 11:
                agent_name = agent_name[:10] + "."
            
            table.add_row(
                f"{icon} {agent_name}",
                str(count),
                is_active
            )
            rows_added += 1
        
        # Fill remaining rows with empty content to maintain exact height
        while rows_added < 10:
            table.add_row("", "", "")
            rows_added += 1
        
        return Panel(
            table,
            title="📊 Agent Activity",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 1),
            height=16,  # Fixed height matching messages panel
            width=35    # Fixed width to prevent expansion
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
            padding=(0, 1),  # Reduced padding
            height=4  # Fixed compact height
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