"""Comprehensive debugging script for the multi-agent system.

This script provides detailed visibility into all states, execution flow,
and decision-making processes of the multi-agent system.
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.syntax import Syntax
from rich.live import Live
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Import the multi-agent system components
from graph.supervisor_graph import create_supervisor_graph, SupervisorGraph
from llm.langchain_adapter import LangChainGeminiAdapter
from agents.general_qa import GeneralQAAgent, ExplicitReActAgent
from agents.research_agent import ResearchAgent
from agents.supervisor import SupervisorAgent


class DebugTracer:
    """Captures and stores debug information during execution."""
    
    def __init__(self):
        self.events = []
        self.current_trace_id = 0
        self.start_time = time.time()
    
    def add_event(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict] = None):
        """Add a debug event."""
        event = {
            "id": self.current_trace_id,
            "timestamp": time.time() - self.start_time,
            "datetime": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
            "metadata": metadata or {}
        }
        self.events.append(event)
        self.current_trace_id += 1
        return event
    
    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type."""
        return [e for e in self.events if e["type"] == event_type]
    
    def save_to_file(self, filename: str):
        """Save debug trace to file."""
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def load_from_file(self, filename: str):
        """Load debug trace from file."""
        with open(filename, 'r') as f:
            self.events = json.load(f)


class DebugAgentSystem:
    """Debug wrapper for the multi-agent system with comprehensive logging."""
    
    def __init__(self, api_key: str, verbose: bool = True):
        self.api_key = api_key
        self.verbose = verbose
        self.console = Console()
        self.tracer = DebugTracer()
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize all system components with debug hooks."""
        self.tracer.add_event("system_init", {"status": "starting"})
        
        try:
            # Create LLM with debug wrapper
            self.llm = self._create_debug_llm(self.api_key)
            
            # Create supervisor graph
            self.graph = create_supervisor_graph(self.api_key)
            
            # Hook into agents for debugging
            self._hook_agents()
            
            self.tracer.add_event("system_init", {"status": "completed"})
            
        except Exception as e:
            self.tracer.add_event("system_init", {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            raise
    
    def _create_debug_llm(self, api_key: str) -> LangChainGeminiAdapter:
        """Create LLM with debug wrapper."""
        original_llm = LangChainGeminiAdapter(api_key)
        
        # Wrap the _call method to capture prompts and responses
        original_call = original_llm._call
        def debug_call(prompt: str, *args, **kwargs):
            call_start = time.time()
            self.tracer.add_event("llm_call", {
                "prompt": prompt,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt
            })
            
            try:
                response = original_call(prompt, *args, **kwargs)
                call_duration = time.time() - call_start
                
                self.tracer.add_event("llm_response", {
                    "response": response,
                    "response_length": len(response),
                    "duration": call_duration,
                    "tokens_per_second": len(response.split()) / call_duration if call_duration > 0 else 0
                })
                
                return response
            except Exception as e:
                self.tracer.add_event("llm_error", {
                    "error": str(e),
                    "duration": time.time() - call_start
                })
                raise
        
        original_llm._call = debug_call
        return original_llm
    
    def _hook_agents(self):
        """Hook into agent methods for debugging."""
        # Hook supervisor routing
        if hasattr(self.graph, 'supervisor'):
            original_route = self.graph.supervisor.route
            def debug_route(query: str, *args, **kwargs):
                self.tracer.add_event("routing_start", {"query": query})
                result = original_route(query, *args, **kwargs)
                self.tracer.add_event("routing_decision", result)
                return result
            self.graph.supervisor.route = debug_route
        
        # Hook general agent Think-Act-Observe
        if hasattr(self.graph, 'general_agent') and hasattr(self.graph.general_agent, 'react_agent'):
            react_agent = self.graph.general_agent.react_agent
            
            # Hook parse output
            original_parse = react_agent._parse_llm_output
            def debug_parse(output: str):
                result = original_parse(output)
                self.tracer.add_event("react_parse", {
                    "input": output,
                    "parsed": result
                })
                return result
            react_agent._parse_llm_output = debug_parse
            
            # Hook tool execution
            original_execute = react_agent._execute_tool
            def debug_execute(tool_name: str, tool_input: str):
                self.tracer.add_event("tool_execution_start", {
                    "tool": tool_name,
                    "input": tool_input
                })
                start_time = time.time()
                try:
                    result = original_execute(tool_name, tool_input)
                    self.tracer.add_event("tool_execution_complete", {
                        "tool": tool_name,
                        "output": result,
                        "duration": time.time() - start_time
                    })
                    return result
                except Exception as e:
                    self.tracer.add_event("tool_execution_error", {
                        "tool": tool_name,
                        "error": str(e),
                        "duration": time.time() - start_time
                    })
                    raise
            react_agent._execute_tool = debug_execute
    
    def debug_query(self, query: str, step_by_step: bool = False) -> Dict[str, Any]:
        """Execute a query with comprehensive debugging."""
        self.tracer = DebugTracer()  # Reset tracer for new query
        query_start = time.time()
        
        self.tracer.add_event("query_start", {"query": query})
        
        if self.verbose:
            self.console.print(f"\n[bold cyan]Debug Query:[/bold cyan] {query}")
            self.console.print("[dim]Starting debug trace...[/dim]\n")
        
        try:
            # Run the query through the graph
            if step_by_step:
                result = self._run_step_by_step(query)
            else:
                result = self.graph.query(query)
            
            query_duration = time.time() - query_start
            
            self.tracer.add_event("query_complete", {
                "result": result,
                "duration": query_duration
            })
            
            # Display results
            if self.verbose:
                self._display_debug_results(result, query_duration)
            
            return result
            
        except Exception as e:
            self.tracer.add_event("query_error", {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "duration": time.time() - query_start
            })
            
            if self.verbose:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
                self.console.print_exception()
            
            raise
    
    def _run_step_by_step(self, query: str) -> Dict[str, Any]:
        """Run query with step-by-step debugging."""
        # This would require modifying the graph execution to pause at each step
        # For now, we'll use the regular execution with detailed logging
        return self.graph.query(query)
    
    def _display_debug_results(self, result: Dict[str, Any], duration: float):
        """Display comprehensive debug results."""
        # Query Summary
        self.console.print("\n[bold green]Query Execution Summary[/bold green]")
        summary_table = Table(show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Total Duration", f"{duration:.2f} seconds")
        summary_table.add_row("Route", result.get('route', 'unknown'))
        summary_table.add_row("Success", "✓" if not result.get('error') else "✗")
        summary_table.add_row("Total Events", str(len(self.tracer.events)))
        
        self.console.print(summary_table)
        
        # Event Timeline
        self.console.print("\n[bold yellow]Event Timeline[/bold yellow]")
        self._display_event_timeline()
        
        # LLM Interactions
        self.console.print("\n[bold magenta]LLM Interactions[/bold magenta]")
        self._display_llm_interactions()
        
        # Tool Executions
        self.console.print("\n[bold cyan]Tool Executions[/bold cyan]")
        self._display_tool_executions()
    
    def _display_event_timeline(self):
        """Display timeline of all events."""
        timeline_table = Table(show_header=True, header_style="bold yellow")
        timeline_table.add_column("Time", style="dim", width=10)
        timeline_table.add_column("Event", style="cyan")
        timeline_table.add_column("Details", style="white")
        
        for event in self.tracer.events[:20]:  # Show first 20 events
            timeline_table.add_row(
                f"{event['timestamp']:.3f}s",
                event['type'],
                str(event['data'])[:80] + "..." if len(str(event['data'])) > 80 else str(event['data'])
            )
        
        if len(self.tracer.events) > 20:
            timeline_table.add_row("...", f"[dim]({len(self.tracer.events) - 20} more events)[/dim]", "")
        
        self.console.print(timeline_table)
    
    def _display_llm_interactions(self):
        """Display all LLM interactions."""
        llm_calls = self.tracer.get_events_by_type("llm_call")
        llm_responses = self.tracer.get_events_by_type("llm_response")
        
        for i, (call, response) in enumerate(zip(llm_calls, llm_responses)):
            self.console.print(f"\n[bold]LLM Call {i+1}[/bold]")
            
            # Show prompt
            prompt_preview = call['data']['prompt_preview']
            self.console.print(Panel(
                prompt_preview,
                title=f"Prompt (length: {call['data']['prompt_length']})",
                expand=False
            ))
            
            # Show response
            if i < len(llm_responses):
                resp_data = response['data']
                self.console.print(Panel(
                    resp_data['response'][:500] + "..." if len(resp_data['response']) > 500 else resp_data['response'],
                    title=f"Response (duration: {resp_data['duration']:.2f}s)",
                    expand=False
                ))
    
    def _display_tool_executions(self):
        """Display all tool executions."""
        tool_starts = self.tracer.get_events_by_type("tool_execution_start")
        tool_completes = self.tracer.get_events_by_type("tool_execution_complete")
        
        if tool_starts:
            tool_table = Table(show_header=True, header_style="bold cyan")
            tool_table.add_column("Tool", style="yellow")
            tool_table.add_column("Input", style="white")
            tool_table.add_column("Output", style="green")
            tool_table.add_column("Duration", style="dim")
            
            for start in tool_starts:
                # Find corresponding complete event
                complete = next((c for c in tool_completes 
                                if c['data']['tool'] == start['data']['tool'] 
                                and c['id'] > start['id']), None)
                
                if complete:
                    tool_table.add_row(
                        start['data']['tool'],
                        start['data']['input'][:50] + "..." if len(start['data']['input']) > 50 else start['data']['input'],
                        complete['data']['output'][:50] + "..." if len(complete['data']['output']) > 50 else complete['data']['output'],
                        f"{complete['data']['duration']:.3f}s"
                    )
            
            self.console.print(tool_table)
    
    def export_debug_data(self, format: str = "json") -> str:
        """Export debug data in various formats."""
        if format == "json":
            filename = f"debug_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.tracer.save_to_file(filename)
            return filename
        
        elif format == "dataframe":
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(self.tracer.events)
            return df
        
        elif format == "markdown":
            # Generate markdown report
            md_content = self._generate_markdown_report()
            filename = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w') as f:
                f.write(md_content)
            return filename
    
    def _generate_markdown_report(self) -> str:
        """Generate a markdown debug report."""
        report = "# Multi-Agent System Debug Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Event Summary
        report += "## Event Summary\n\n"
        event_types = {}
        for event in self.tracer.events:
            event_types[event['type']] = event_types.get(event['type'], 0) + 1
        
        for event_type, count in event_types.items():
            report += f"- **{event_type}**: {count} events\n"
        
        # Timeline
        report += "\n## Event Timeline\n\n"
        report += "| Time | Event Type | Details |\n"
        report += "|------|------------|----------|\n"
        
        for event in self.tracer.events[:50]:
            details = str(event['data'])[:100].replace('|', '\\|')
            report += f"| {event['timestamp']:.3f}s | {event['type']} | {details} |\n"
        
        return report
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics from debug data."""
        metrics = {
            "total_duration": 0,
            "llm_calls": 0,
            "llm_total_duration": 0,
            "tool_executions": 0,
            "tool_total_duration": 0,
            "errors": 0
        }
        
        # Calculate metrics
        if self.tracer.events:
            metrics["total_duration"] = self.tracer.events[-1]["timestamp"]
        
        llm_responses = self.tracer.get_events_by_type("llm_response")
        metrics["llm_calls"] = len(llm_responses)
        metrics["llm_total_duration"] = sum(r['data']['duration'] for r in llm_responses)
        
        tool_completes = self.tracer.get_events_by_type("tool_execution_complete")
        metrics["tool_executions"] = len(tool_completes)
        metrics["tool_total_duration"] = sum(t['data']['duration'] for t in tool_completes)
        
        error_events = [e for e in self.tracer.events if 'error' in e['type']]
        metrics["errors"] = len(error_events)
        
        # Calculate percentages
        if metrics["total_duration"] > 0:
            metrics["llm_percentage"] = (metrics["llm_total_duration"] / metrics["total_duration"]) * 100
            metrics["tool_percentage"] = (metrics["tool_total_duration"] / metrics["total_duration"]) * 100
        
        return metrics
    
    def visualize_execution_flow(self):
        """Create a visual representation of the execution flow."""
        tree = Tree("[bold]Execution Flow[/bold]")
        
        current_branch = tree
        indent_stack = [tree]
        
        for event in self.tracer.events:
            if event['type'] == 'query_start':
                query_branch = current_branch.add(f"[cyan]Query: {event['data']['query'][:50]}...[/cyan]")
                indent_stack.append(query_branch)
                current_branch = query_branch
            
            elif event['type'] == 'routing_decision':
                current_branch.add(f"[yellow]→ Routed to: {event['data']['route']}[/yellow]")
            
            elif event['type'] == 'react_parse':
                parsed_type = event['data']['parsed']['type']
                if parsed_type == 'action':
                    action_branch = current_branch.add(f"[magenta]Action: {event['data']['parsed']['action']}[/magenta]")
                    indent_stack.append(action_branch)
                    current_branch = action_branch
                elif parsed_type == 'final_answer':
                    current_branch.add(f"[green]Final Answer[/green]")
            
            elif event['type'] == 'tool_execution_complete':
                current_branch.add(f"[blue]Tool Result: {event['data']['output'][:50]}...[/blue]")
                if len(indent_stack) > 1:
                    indent_stack.pop()
                    current_branch = indent_stack[-1]
        
        self.console.print(tree)


# Notebook-friendly functions
def create_debug_system(api_key: Optional[str] = None, verbose: bool = True) -> DebugAgentSystem:
    """Create a debug system instance (notebook-friendly)."""
    if not api_key:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No API key provided and GEMINI_API_KEY not found")
    
    return DebugAgentSystem(api_key, verbose)


def debug_query(system: DebugAgentSystem, query: str, show_flow: bool = True) -> Dict[str, Any]:
    """Run a debug query with optional flow visualization (notebook-friendly)."""
    result = system.debug_query(query)
    
    if show_flow:
        system.visualize_execution_flow()
    
    # Display performance metrics
    metrics = system.analyze_performance()
    print("\nPerformance Metrics:")
    print(f"- Total Duration: {metrics['total_duration']:.2f}s")
    print(f"- LLM Calls: {metrics['llm_calls']} ({metrics.get('llm_percentage', 0):.1f}% of time)")
    print(f"- Tool Executions: {metrics['tool_executions']} ({metrics.get('tool_percentage', 0):.1f}% of time)")
    
    return result


# Example usage
if __name__ == "__main__":
    # Load environment
    load_dotenv()
    
    # Create debug system
    debug_system = create_debug_system()
    
    # Example queries to debug
    test_queries = [
        "What is 25 * 47?",
        "What's the current price of Bitcoin?",
        "Compare machine learning and deep learning"
    ]
    
    console = Console()
    
    for query in test_queries[:1]:  # Test with first query
        console.print(f"\n[bold blue]Testing Query:[/bold blue] {query}")
        console.print("-" * 80)
        
        # Run debug query
        result = debug_query(debug_system, query)
        
        # Export debug data
        json_file = debug_system.export_debug_data("json")
        console.print(f"\n[green]Debug trace saved to:[/green] {json_file}")
        
        # Generate markdown report
        md_file = debug_system.export_debug_data("markdown")
        console.print(f"[green]Debug report saved to:[/green] {md_file}")
        
        # Show performance analysis
        metrics = debug_system.analyze_performance()
        console.print("\n[bold]Performance Analysis:[/bold]")
        for key, value in metrics.items():
            if isinstance(value, float):
                console.print(f"  {key}: {value:.2f}")
            else:
                console.print(f"  {key}: {value}") 