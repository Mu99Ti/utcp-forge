from __future__ import annotations
import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console

from utcp_forge.extractors.fastapi_ast import FastAPIASTExtractor
from utcp_forge.extractors.openapi import OpenApiExtractor
from utcp_forge.indexer.symbol_table import SymbolTable
from utcp_forge.indexer.host_detector import HostDetector
from utcp_forge.indexer.backend_detector import BackendDetector
from utcp_forge.agent.investigator import RouteInvestigatorAgent
from utcp_forge.compiler.manual_builder import UtcpCompiler
from utcp_forge.ui.console import render_tool_summary

app = typer.Typer(
    name="utcp-forge",
    help="AI-powered tool that investigates codebases to synthesize production-ready UTCP manuals."
)
console = Console()

@app.command()
def scan(
    target: str = typer.Argument(..., help="Path to repository root, backend directory, or OpenAPI spec file/URL"),
    manual_name: str = typer.Option("app_service", "--manual-name", "-n", help="Namespace for manual (e.g. order_service)"),
    output: str = typer.Option("utcp.json", "--output", "-o", help="Target path for utcp.json"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-u", help="Base URL for API routes (auto-detected if omitted)"),
    llm_base_url: Optional[str] = typer.Option(None, "--llm-base-url", help="Custom OpenAI-compatible LLM endpoint (e.g. http://127.0.0.1:20128/v1)"),
    llm_api_key: Optional[str] = typer.Option(None, "--llm-api-key", help="API key for custom LLM endpoint"),
    model: str = typer.Option("free", "--model", "-m", help="LLM model for semantic curation"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress terminal output")
):
    """Scan a codebase or OpenAPI spec, investigate routes via LangChain DeepAgent, and generate utcp.json."""
    if not quiet:
        console.print(f"[bold cyan]Scanning target:[/bold cyan] {target}")

    target_path = Path(target).resolve()
    routes = []
    symbol_table = None
    resolved_base_url = base_url

    # Case A: Live URL or standalone OpenAPI / Swagger file
    if target.startswith("http://") or target.startswith("https://") or (target_path.is_file() and target_path.suffix in (".json", ".yaml", ".yml")):
        if not quiet:
            console.print("[dim]Detected OpenAPI/Swagger spec...[/dim]")
        extractor = OpenApiExtractor(target)
        routes = extractor.scan()
        if not resolved_base_url:
            resolved_base_url = "http://localhost:8000"

    # Case B: Repository or Codebase Directory
    else:
        # Detect backend service directories inside monorepo/full-stack project
        detected_backend_dirs = BackendDetector.locate_backend_dirs(str(target_path))
        
        if not quiet:
            if len(detected_backend_dirs) == 1 and detected_backend_dirs[0] != target_path:
                console.print(f"[dim]Auto-detected backend directory:[/dim] [cyan]{detected_backend_dirs[0]}[/cyan]")
            elif len(detected_backend_dirs) > 1:
                console.print(f"[dim]Auto-detected {len(detected_backend_dirs)} backend services across repository.[/dim]")

        # Auto-detect base URL from project configurations
        if not resolved_base_url:
            resolved_base_url = HostDetector.detect_base_url(str(target_path))
            if not quiet:
                console.print(f"[dim]Auto-detected base URL:[/dim] [cyan]{resolved_base_url}[/cyan]")

        # Scan each detected backend directory
        all_routes = []
        for b_dir in detected_backend_dirs:
            sym_table = SymbolTable(str(b_dir))
            if not symbol_table:
                symbol_table = sym_table
            extractor = FastAPIASTExtractor(str(b_dir))
            all_routes.extend(extractor.scan())

        # Deduplicate routes by method + path
        seen_routes = set()
        for r in all_routes:
            key = (r.method, r.path)
            if key not in seen_routes:
                seen_routes.add(key)
                routes.append(r)

    if not routes:
        console.print("[bold red]No API routes found in target repository or directories.[/bold red]")
        raise typer.Exit(code=1)

    if not quiet:
        console.print(f"[green]Found {len(routes)} raw endpoints across target codebase.[/green]")
        console.print(f"[dim]Investigating with DeepAgent ({model})...[/dim]")

    # 2. Agent Investigation
    agent = RouteInvestigatorAgent(
        model_name=model,
        base_url=llm_base_url,
        api_key=llm_api_key,
        symbol_table=symbol_table
    )
    enriched_tools = [agent.investigate(r) for r in routes]

    # 3. UI Display
    if not quiet:
        render_tool_summary(enriched_tools)

    # 4. Compile UTCP Manual with Expert Namespacing
    manual = UtcpCompiler.compile(
        enriched_tools,
        manual_name=manual_name,
        base_url=resolved_base_url or "http://localhost:8000"
    )
    UtcpCompiler.save_to_file(manual, output)

    if not quiet:
        console.print(f"\n[bold green]Successfully generated UTCP manual with {len(manual.tools)} tools at:[/bold green] [bold underline]{output}[/bold underline]\n")

if __name__ == "__main__":
    app()
