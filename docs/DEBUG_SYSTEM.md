# Multi-Agent System Debug Tools

## Overview

The debug system provides comprehensive visibility into the multi-agent system's execution flow, state transitions, and decision-making processes. It captures every aspect of query processing, from routing decisions to tool executions.

## Features

### 1. Comprehensive Event Tracking
- **System Initialization**: Tracks system startup and component initialization
- **Routing Decisions**: Captures how queries are routed to agents
- **LLM Interactions**: Records all prompts and responses with timing data
- **Think-Act-Observe Cycle**: Detailed tracking of the React agent's reasoning
- **Tool Executions**: Monitors all tool calls with inputs, outputs, and durations

### 2. Performance Analysis
- Total execution time breakdown
- LLM call statistics and durations
- Tool execution metrics
- Error tracking and diagnostics
- Performance bottleneck identification

### 3. Visualization and Export
- Execution flow tree visualization
- Event timeline displays
- Export to JSON, DataFrame, or Markdown
- Jupyter notebook-friendly interface

## Usage

### Basic Setup

```python
from debug_agent_system import create_debug_system, debug_query

# Create debug system
debug_system = create_debug_system()

# Run a debug query
result = debug_query(debug_system, "What is 25 * 47?")
```

### Command Line Usage

```bash
# Run the debug script
python debug_agent_system.py

# This will execute test queries and generate debug reports
```

### Jupyter Notebook Usage

```python
# Cell 1: Import and setup
from debug_agent_system import create_debug_system
debug_system = create_debug_system(verbose=True)

# Cell 2: Analyze a query
from debug_notebook_example import analyze_query
result, df = analyze_query("What's the weather in Paris?")

# Cell 3: Batch analysis
from debug_notebook_example import batch_analyze
queries = ["What is 2+2?", "Explain AI", "Current Bitcoin price"]
results = batch_analyze(queries)

# Cell 4: Deep dive into execution
from debug_notebook_example import deep_dive
events = deep_dive("Calculate compound interest")
```

## Key Components

### DebugTracer
Captures and stores all debug events during execution:

```python
class DebugTracer:
    def add_event(event_type, data, metadata=None)
    def get_events_by_type(event_type)
    def save_to_file(filename)
    def load_from_file(filename)
```

### DebugAgentSystem
Main debugging wrapper that hooks into the multi-agent system:

```python
class DebugAgentSystem:
    def debug_query(query, step_by_step=False)
    def analyze_performance()
    def visualize_execution_flow()
    def export_debug_data(format="json")
```

## Event Types

1. **System Events**
   - `system_init`: System initialization
   - `query_start`: Query processing begins
   - `query_complete`: Query processing ends
   - `query_error`: Query processing error

2. **Routing Events**
   - `routing_start`: Routing decision begins
   - `routing_decision`: Route determined

3. **LLM Events**
   - `llm_call`: LLM prompt sent
   - `llm_response`: LLM response received
   - `llm_error`: LLM call error

4. **React Agent Events**
   - `react_parse`: Output parsing result
   - `tool_execution_start`: Tool execution begins
   - `tool_execution_complete`: Tool execution ends
   - `tool_execution_error`: Tool execution error

## Debug Output Examples

### Event Timeline
Shows chronological sequence of all events:
```
Time     | Event              | Details
---------|--------------------|---------
0.000s   | query_start        | {'query': 'What is 25 * 47?'}
0.001s   | routing_start      | {'query': 'What is 25 * 47?'}
1.887s   | routing_decision   | {'route': 'general', 'reasoning': '...'}
3.396s   | react_parse        | {'type': 'final_answer', ...}
3.397s   | query_complete     | {'result': {...}, 'duration': 3.397}
```

### Execution Flow Tree
Visual representation of execution path:
```
Execution Flow
└── Query: What is 25 * 47?
    ├── → Routed to: general
    ├── Action: web_search
    │   └── Tool Result: Current price is $50,000...
    └── Final Answer
```

### Performance Metrics
```
Performance Metrics:
- Total Duration: 5.23s
- LLM Calls: 3 (65.2% of time)
- Tool Executions: 2 (28.4% of time)
```

## Export Formats

### JSON Export
Complete event trace with all metadata:
```json
{
  "id": 0,
  "timestamp": 0.0,
  "datetime": "2024-06-01T12:00:00",
  "type": "query_start",
  "data": {"query": "What is 25 * 47?"},
  "metadata": {}
}
```

### Markdown Report
Human-readable summary with tables and statistics.

### DataFrame Export
For data analysis in pandas:
```python
df = debug_system.export_debug_data("dataframe")
# Analyze with pandas operations
df.groupby('type')['timestamp'].count()
```

## Advanced Features

### Step-by-Step Debugging
```python
# Enable step-by-step mode (future feature)
result = debug_system.debug_query(query, step_by_step=True)
```

### Custom Event Hooks
```python
# Add custom event tracking
def custom_hook(event):
    if event['type'] == 'llm_call':
        print(f"LLM called with {len(event['data']['prompt'])} chars")

debug_system.add_event_hook(custom_hook)
```

### Performance Profiling
```python
# Get detailed performance breakdown
metrics = debug_system.analyze_performance()
bottlenecks = debug_system.identify_bottlenecks()
```

## Debugging Tips

1. **For Slow Queries**: Check if complex queries are being routed to the Research Agent unnecessarily
2. **For Errors**: Look for `error` event types in the trace
3. **For Tool Issues**: Check `tool_execution_error` events
4. **For LLM Issues**: Examine prompt/response pairs in LLM events

## Integration with Development Workflow

1. **Development**: Use verbose mode to see real-time execution
2. **Testing**: Export traces for regression testing
3. **Production**: Use minimal logging with selective event capture
4. **Analysis**: Export to DataFrame for statistical analysis 