from __future__ import annotations
from typing import List
from rich.console import Console
from rich.table import Table
from utcp_forge.models.ir import EnrichedToolIR

console = Console()

def render_tool_summary(tools: List[EnrichedToolIR]) -> None:
    table = Table(title="UTCP-Forge Agent Tool Discovery", show_header=True, header_style="bold magenta")
    table.add_column("Status", style="dim", width=10)
    table.add_column("Method", width=8)
    table.add_column("Path", width=30)
    table.add_column("Tool Name", width=25)
    table.add_column("Agent Intent & Description", style="italic")

    for t in tools:
        if t.should_include:
            status = "[green]INCLUDE[/green]"
            method_color = "cyan" if t.method == "GET" else "yellow" if t.method in ("POST", "PUT") else "red"
            table.add_row(
                status,
                f"[{method_color}]{t.method}[/{method_color}]",
                t.path,
                t.name,
                t.description[:60] + ("..." if len(t.description) > 60 else "")
            )
        else:
            table.add_row(
                "[red]SKIP[/red]",
                f"[dim]{t.method}[/dim]",
                t.path,
                t.name,
                f"[dim]({t.exclusion_reason or 'Excluded'})[/dim]"
            )

    console.print(table)
