"""Main CLI entry point for the multi-agent system."""

import os
import sys
import signal
from typing import Optional
from dotenv import load_dotenv
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from graph.supervisor_graph import create_supervisor_graph, run_query


console = Console()


def signal_handler(sig, frame, graph=None):
    """Handle Ctrl+C gracefully."""
    if graph and hasattr(graph, 'get_history'):
        history_count = len(graph.get_history())
        console.print(f"\n\n[yellow]Session interrupted.[/yellow] {history_count} interactions recorded.")
    else:
        console.print("\n\n[yellow]Session interrupted.[/yellow]")
    console.print("[dim]Conversation history cleared.[/dim]")
    console.print("[yellow]Goodbye![/yellow] 👋\n")
    sys.exit(0)


def display_result(result: dict):
    """Display query result in a formatted way."""
    # Header
    console.print("\n" + "="*80)
    console.print(f"[bold cyan]Query:[/bold cyan] {result['query']}")
    console.print(f"[bold yellow]Routed to:[/bold yellow] {result['route']} agent")
    console.print(f"[bold yellow]Reasoning:[/bold yellow] {result['routing_reasoning']}")
    console.print("="*80 + "\n")
    
    # Response
    console.print(Panel(result['response'], title="[bold green]Response[/bold green]", expand=False))
    
    # Steps taken (if any)
    if result['steps']:
        console.print("\n[bold magenta]Steps Taken:[/bold magenta]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tool", style="cyan", no_wrap=True)
        table.add_column("Input", style="white")
        table.add_column("Output", style="green")
        
        for step in result['steps']:
            output = step['output']
            if len(output) > 100:
                output = output[:97] + "..."
            table.add_row(
                step['tool'],
                step['input'][:50] + "..." if len(step['input']) > 50 else step['input'],
                output
            )
        
        console.print(table)
    
    # Error (if any)
    if result.get('error'):
        console.print(f"\n[bold red]Error:[/bold red] {result['error']}")


@click.command()
@click.option('--api-key', envvar='GEMINI_API_KEY', help='Gemini API key')
@click.option('--query', '-q', help='Query to process (interactive mode if not provided)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(api_key: Optional[str], query: Optional[str], verbose: bool):
    """Multi-Agent System CLI - Route queries to specialized AI agents."""
    
    # Load environment variables
    load_dotenv()
    
    # Get API key
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            console.print("[bold red]Error:[/bold red] No API key found. Set GEMINI_API_KEY environment variable or use --api-key option.")
            sys.exit(1)
    
    # Welcome message
    console.print("\n[bold cyan]Multi-Agent System[/bold cyan] 🤖")
    console.print("Route queries to specialized AI agents for optimal responses.\n")
    
    try:
        # Create supervisor graph
        console.print("[dim]Initializing agents...[/dim]")
        graph = create_supervisor_graph(api_key)
        console.print("[green]✓[/green] Agents initialized successfully!\n")
        
        # Register signal handler with graph reference
        signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, graph))
        
        # Single query mode
        if query:
            if verbose:
                console.print(f"[dim]Processing query: {query}[/dim]\n")
            
            result = run_query(graph, query)
            display_result(result)
        
        # Interactive mode
        else:
            console.print("[bold]Interactive Mode[/bold] - Type 'exit' or 'quit' to end")
            console.print("[dim]Commands: 'history' - show conversation history, 'clear' - clear history[/dim]\n")
            
            while True:
                # Get user input
                user_query = Prompt.ask("\n[bold cyan]Enter your query[/bold cyan]")
                
                # Check for exit
                if user_query.lower() in ['exit', 'quit', 'q']:
                    history_count = len(graph.get_history())
                    console.print(f"\n[yellow]Session ended.[/yellow] {history_count} interactions recorded.")
                    console.print("[yellow]Goodbye![/yellow] 👋")
                    break
                
                # Check for history command
                if user_query.lower() == 'history':
                    console.print("\n" + graph.get_history_summary())
                    continue
                
                # Check for clear command
                if user_query.lower() == 'clear':
                    graph.clear_history()
                    console.print("[green]✓[/green] Conversation history cleared.")
                    continue
                
                # Process query
                try:
                    if verbose:
                        console.print(f"\n[dim]Processing...[/dim]")
                    
                    result = run_query(graph, user_query)
                    display_result(result)
                
                except Exception as e:
                    console.print(f"\n[bold red]Error processing query:[/bold red] {str(e)}")
                    if verbose:
                        console.print_exception()
    
    except Exception as e:
        console.print(f"\n[bold red]Error initializing system:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@click.group()
def cli():
    """Multi-Agent System CLI"""
    pass


@cli.command()
@click.option('--port', '-p', default=8000, help='Port to run the server on')
def serve(port: int):
    """Run the LangGraph web interface (if available)."""
    console.print(f"\n[bold cyan]Starting LangGraph Studio on port {port}...[/bold cyan]")
    
    try:
        # Try to import and run LangGraph Studio
        from langgraph.studio import run_studio
        from graph.supervisor_graph import create_supervisor_graph
        
        # Load API key
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in environment.")
            sys.exit(1)
        
        # Create graph
        graph = create_supervisor_graph(api_key)
        
        # Run studio
        run_studio(graph, port=port)
        
    except ImportError:
        console.print("[bold yellow]LangGraph Studio not available.[/bold yellow]")
        console.print("To use the web interface, install langgraph[studio]:")
        console.print("  pip install langgraph[studio]")
    except Exception as e:
        console.print(f"[bold red]Error starting server:[/bold red] {str(e)}")
        sys.exit(1)


@cli.command()
def info():
    """Display information about available agents and tools."""
    console.print("\n[bold cyan]Multi-Agent System Information[/bold cyan]\n")
    
    # Agents
    agents_table = Table(title="Available Agents", show_header=True, header_style="bold magenta")
    agents_table.add_column("Agent", style="cyan", no_wrap=True)
    agents_table.add_column("Purpose", style="white")
    agents_table.add_column("Tools", style="green")
    
    agents_table.add_row(
        "Supervisor",
        "Routes queries to appropriate agents",
        "None (routing only)"
    )
    agents_table.add_row(
        "General Q&A",
        "Handles simple queries and calculations",
        "Python REPL, Web Search"
    )
    agents_table.add_row(
        "Research",
        "Complex research with planning",
        "Wikipedia, ArXiv, Web Search, Python REPL"
    )
    
    console.print(agents_table)
    
    # Example queries
    console.print("\n[bold yellow]Example Queries:[/bold yellow]")
    console.print("• What is 25 * 47? (→ General Q&A)")
    console.print("• What's the weather in Paris? (→ General Q&A)")
    console.print("• Explain quantum computing and its recent developments (→ Research)")
    console.print("• Compare different machine learning architectures (→ Research)")


if __name__ == "__main__":
    # Check if running with 'serve' or 'info' command
    if len(sys.argv) > 1 and sys.argv[1] in ['serve', 'info']:
        cli()
    else:
        main() 