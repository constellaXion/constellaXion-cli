from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

console = Console()


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✅ {message}[/bold green]")


def print_error(message: str, error: str = None) -> None:
    """Print error message."""
    console.print(f"[bold red]❌ {message}[/bold red]")
    if error:
        console.print(f"[red]Error: {error}[/red]")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[cyan]{message}[/cyan]")


def print_resource_table(
    title: str, resources: List[Dict[str, Any]], provider: str, region: str
) -> None:
    """Print a table of terraform resources."""
    table = Table(
        title=f"{title} ({provider.upper()} - {region})",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Resource Type", style="dim", width=30, no_wrap=False)
    table.add_column("Name / Address", style="cyan", min_width=20, no_wrap=False)
    table.add_column("Status", style="green", width=15)
    table.add_column("Source", style="dim", width=15)

    for resource in resources:
        resource_type = str(resource.get("resource_type", "Unknown"))
        name = str(resource.get("name", "Unknown"))
        status = str(resource.get("status", "Unknown"))
        source = str(resource.get("source", "Unknown"))

        table.add_row(resource_type, name, status, source)

    console.print(table)
    console.print(f"\nTotal: {len(resources)} resources in {region}")


def print_operations_table(title: str, operations: List[Dict[str, Any]]) -> None:
    """Print a table of operation results."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Operation", style="bold blue", width=30)
    table.add_column("Status", style="green", width=15)
    table.add_column("Details", style="dim")

    for op in operations:
        status_style = "green" if op.get("success") else "red"
        status_text = "SUCCESS" if op.get("success") else "FAILED"

        table.add_row(
            op.get("name", "Unknown"),
            f"[{status_style}]{status_text}[/{status_style}]",
            op.get("details", ""),
        )

    console.print(table)
