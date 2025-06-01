"""
Example usage of the debug system in a Jupyter notebook environment.

This script demonstrates how to use the debugging system for observing
the multi-agent system's behavior, states, and execution flow.
"""

# Cell 1: Setup and imports
import os
import sys
from dotenv import load_dotenv
import pandas as pd
import json
from IPython.display import display, HTML, Markdown
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path if needed
sys.path.append('.')

from debug_agent_system import create_debug_system, debug_query


# Cell 2: Initialize the debug system
load_dotenv()
debug_system = create_debug_system(verbose=True)
print("Debug system initialized!")


# Cell 3: Run a simple query and analyze
def analyze_query(query: str):
    """Run a query and display comprehensive analysis."""
    print(f"\n{'='*80}")
    print(f"Analyzing Query: {query}")
    print('='*80)
    
    # Run the query
    result = debug_query(debug_system, query, show_flow=True)
    
    # Get the debug trace as DataFrame
    df = debug_system.export_debug_data("dataframe")
    
    # Display event type distribution
    event_counts = df['type'].value_counts()
    print("\nEvent Type Distribution:")
    print(event_counts)
    
    # Create visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Event timeline
    ax1 = axes[0, 0]
    ax1.scatter(df['timestamp'], df['type'], alpha=0.6)
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Event Type')
    ax1.set_title('Event Timeline')
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Event type pie chart
    ax2 = axes[0, 1]
    event_counts.plot(kind='pie', ax=ax2, autopct='%1.1f%%')
    ax2.set_title('Event Type Distribution')
    ax2.set_ylabel('')
    
    # Duration analysis for LLM calls
    ax3 = axes[1, 0]
    llm_events = df[df['type'] == 'llm_response']
    if not llm_events.empty:
        durations = [e['duration'] for e in llm_events['data']]
        ax3.bar(range(len(durations)), durations)
        ax3.set_xlabel('LLM Call #')
        ax3.set_ylabel('Duration (seconds)')
        ax3.set_title('LLM Call Durations')
    
    # Tool execution analysis
    ax4 = axes[1, 1]
    tool_events = df[df['type'] == 'tool_execution_complete']
    if not tool_events.empty:
        tool_names = [e['tool'] for e in tool_events['data']]
        tool_durations = [e['duration'] for e in tool_events['data']]
        ax4.bar(tool_names, tool_durations)
        ax4.set_xlabel('Tool')
        ax4.set_ylabel('Duration (seconds)')
        ax4.set_title('Tool Execution Times')
    
    plt.tight_layout()
    plt.show()
    
    return result, df


# Cell 4: Interactive query debugging
def interactive_debug():
    """Interactive debugging session."""
    while True:
        query = input("\nEnter query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        
        try:
            result, df = analyze_query(query)
            
            # Show detailed steps
            print("\n" + "-"*40)
            print("DETAILED EXECUTION STEPS:")
            print("-"*40)
            
            for idx, event in enumerate(debug_system.tracer.events):
                if event['type'] in ['routing_decision', 'react_parse', 'tool_execution_complete']:
                    print(f"\n[{idx}] {event['type']} @ {event['timestamp']:.3f}s")
                    print(f"Data: {json.dumps(event['data'], indent=2)[:200]}...")
            
            # Export options
            export = input("\nExport debug data? (json/markdown/no): ").lower()
            if export == 'json':
                filename = debug_system.export_debug_data('json')
                print(f"Exported to: {filename}")
            elif export == 'markdown':
                filename = debug_system.export_debug_data('markdown')
                print(f"Exported to: {filename}")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


# Cell 5: Batch analysis of queries
def batch_analyze(queries: list):
    """Analyze multiple queries and compare performance."""
    results = []
    
    for query in queries:
        print(f"\nProcessing: {query}")
        result = debug_system.debug_query(query, step_by_step=False)
        metrics = debug_system.analyze_performance()
        
        results.append({
            'query': query,
            'route': result.get('route', 'unknown'),
            'total_duration': metrics['total_duration'],
            'llm_calls': metrics['llm_calls'],
            'tool_executions': metrics['tool_executions'],
            'errors': metrics['errors']
        })
    
    # Create comparison DataFrame
    df_results = pd.DataFrame(results)
    
    # Display results
    print("\n" + "="*80)
    print("BATCH ANALYSIS RESULTS")
    print("="*80)
    display(df_results)
    
    # Create comparison visualizations
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Duration by route
    ax1 = axes[0, 0]
    df_results.groupby('route')['total_duration'].mean().plot(kind='bar', ax=ax1)
    ax1.set_title('Average Duration by Route')
    ax1.set_ylabel('Duration (seconds)')
    
    # LLM calls comparison
    ax2 = axes[0, 1]
    ax2.bar(range(len(queries)), df_results['llm_calls'])
    ax2.set_xlabel('Query Index')
    ax2.set_ylabel('LLM Calls')
    ax2.set_title('LLM Calls per Query')
    
    # Tool executions
    ax3 = axes[1, 0]
    ax3.bar(range(len(queries)), df_results['tool_executions'])
    ax3.set_xlabel('Query Index')
    ax3.set_ylabel('Tool Executions')
    ax3.set_title('Tool Executions per Query')
    
    # Duration scatter
    ax4 = axes[1, 1]
    ax4.scatter(df_results['llm_calls'], df_results['total_duration'], 
                s=df_results['tool_executions']*50 + 10, alpha=0.6)
    ax4.set_xlabel('LLM Calls')
    ax4.set_ylabel('Total Duration (seconds)')
    ax4.set_title('Duration vs LLM Calls (size = tool executions)')
    
    plt.tight_layout()
    plt.show()
    
    return df_results


# Cell 6: Deep dive into a specific execution
def deep_dive(query: str):
    """Deep dive analysis of a single query execution."""
    print(f"\nDEEP DIVE ANALYSIS: {query}")
    print("="*80)
    
    # Run query
    result = debug_system.debug_query(query)
    
    # Extract all events
    events = debug_system.tracer.events
    
    # Create detailed timeline
    print("\nDETAILED TIMELINE:")
    print("-"*80)
    
    for event in events:
        timestamp = f"{event['timestamp']:.3f}s"
        event_type = event['type']
        
        # Format based on event type
        if event_type == 'routing_decision':
            print(f"{timestamp} | ROUTING → {event['data']['route']} | {event['data']['reasoning']}")
        
        elif event_type == 'llm_call':
            prompt_preview = event['data']['prompt_preview'][:100].replace('\n', ' ')
            print(f"{timestamp} | LLM CALL | {prompt_preview}...")
        
        elif event_type == 'llm_response':
            response_preview = event['data']['response'][:100].replace('\n', ' ')
            duration = event['data']['duration']
            print(f"{timestamp} | LLM RESP ({duration:.2f}s) | {response_preview}...")
        
        elif event_type == 'react_parse':
            parsed_type = event['data']['parsed']['type']
            print(f"{timestamp} | PARSE → {parsed_type}")
        
        elif event_type == 'tool_execution_start':
            tool = event['data']['tool']
            input_preview = str(event['data']['input'])[:50]
            print(f"{timestamp} | TOOL START: {tool} | Input: {input_preview}...")
        
        elif event_type == 'tool_execution_complete':
            tool = event['data']['tool']
            duration = event['data']['duration']
            output_preview = str(event['data']['output'])[:50]
            print(f"{timestamp} | TOOL DONE: {tool} ({duration:.3f}s) | Output: {output_preview}...")
    
    # State transitions
    print("\n\nSTATE TRANSITIONS:")
    print("-"*80)
    
    state_events = [e for e in events if e['type'] in ['routing_decision', 'react_parse']]
    for i, event in enumerate(state_events):
        if event['type'] == 'routing_decision':
            print(f"{i}. Route to {event['data']['route']} agent")
        elif event['type'] == 'react_parse':
            parsed = event['data']['parsed']
            if parsed['type'] == 'action':
                print(f"{i}. Think → Act ({parsed['action']})")
            elif parsed['type'] == 'final_answer':
                print(f"{i}. Think → Final Answer")
    
    return events


# Cell 7: Example usage
if __name__ == "__main__":
    # Example 1: Simple query analysis
    print("Example 1: Simple Query Analysis")
    result, df = analyze_query("What is 25 * 47?")
    
    # Example 2: Batch analysis
    print("\n\nExample 2: Batch Analysis")
    test_queries = [
        "What is 2 + 2?",
        "What's the weather in Paris?",
        "Explain quantum computing"
    ]
    batch_results = batch_analyze(test_queries)
    
    # Example 3: Deep dive
    print("\n\nExample 3: Deep Dive")
    events = deep_dive("Calculate the area of a circle with radius 5")
    
    # Example 4: Interactive mode (uncomment to use)
    # interactive_debug() 