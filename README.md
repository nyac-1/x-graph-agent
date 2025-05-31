# Multi-Agent System with LangGraph

A sophisticated multi-agent system using LangGraph that intelligently routes queries to specialized agents for optimal responses.

## Documentation

- **[System Workflow & Architecture](docs/SYSTEM_WORKFLOW.md)** - Comprehensive visual guide to query flow and context management
- **[LangGraph Implementation Details](docs/LANGGRAPH_DETAILS.md)** - Deep dive into LangGraph internals and state management
- **[Conversation History Feature](docs/CONVERSATION_HISTORY.md)** - How the system maintains context across interactions
- **[Architecture Overview](docs/ARCHITECTURE.md)** - High-level system design

## Features

- **Intelligent Query Routing**: Supervisor agent analyzes queries and routes them to the most appropriate specialized agent
- **Multiple Specialized Agents**:
  - **General Q&A Agent**: Handles simple queries, calculations, and web searches
  - **Research Agent**: Conducts multi-step research using academic sources, web search, and data analysis
- **Tool Integration**: Python REPL, Web Search, Wikipedia, ArXiv paper search
- **Beautiful CLI**: Rich terminal interface with formatted outputs and tables
- **Conversation History**: In-memory session history that tracks all interactions

## Architecture

```
┌─────────────┐
│  Supervisor │ ──> Routes queries based on complexity
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌──────┐ ┌──────────┐
│General│ │ Research │
│  Q&A  │ │  Agent   │
└──────┘ └──────────┘
   │         │
   │         ├── Wikipedia
   │         ├── ArXiv
   │         ├── Web Search
   │         └── Python REPL
   │
   ├── Web Search
   └── Python REPL
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up API Key

Create a `.env` file:
```env
GEMINI_API_KEY=your-api-key-here
```

### 3. Run the System

Interactive mode:
```bash
python main.py
```

Single query:
```bash
python main.py -q "What is 25 * 47?"
```

## Usage Examples

### Simple Calculations (→ General Q&A)
```bash
python main.py -q "What is 25 * 47?"
python main.py -q "Calculate the compound interest on $1000 at 5% for 10 years"
```

### Current Information (→ General Q&A)
```bash
python main.py -q "What's the weather in Paris?"
python main.py -q "Who won the 2024 Super Bowl?"
```

### Research Tasks (→ Research Agent)
```bash
python main.py -q "Explain the latest developments in quantum computing"
python main.py -q "Compare transformer and LSTM architectures for NLP"
```

## Interactive Commands

When running in interactive mode, you can use these commands:

- `history` - Display conversation history for the current session
- `clear` - Clear conversation history
- `exit`/`quit` - End the session

## How It Works

1. **Query Analysis**: The Supervisor agent analyzes your query to determine its complexity and requirements
2. **Intelligent Routing**: Based on the analysis, queries are routed to:
   - **General Q&A**: For simple questions, calculations, and direct lookups
   - **Research Agent**: For complex topics requiring multiple sources and analysis
3. **Tool Execution**: Agents use their available tools to gather information and process data
4. **Response Generation**: Results are formatted and presented in a clear, readable format

## Conversation History

The system maintains an in-memory conversation history during each session:

- Tracks all queries, responses, and routing decisions
- Shows timestamps and reasoning for each interaction
- Accessible via the `history` command in interactive mode
- Automatically cleared when the session ends (stateless design)

## System Components

### 1. Supervisor Agent
- Analyzes query complexity
- Routes to appropriate specialist agent
- Tracks conversation history

### 2. General Q&A Agent
- Handles simple queries
- Tools: Python REPL, Web Search
- Best for: calculations, facts, current info

### 3. Research Agent
- Conducts multi-step research
- Tools: Wikipedia, ArXiv, Web Search, Python REPL
- Best for: complex topics, comparisons, analysis

## Project Structure

```
x-graph-agent/
├── agents/             # Agent implementations
├── graph/              # LangGraph workflows
├── llm/                # LLM integration
├── prompts/            # System prompts
├── tools/              # Tool wrappers
├── main.py             # CLI entry point
└── requirements.txt    # Dependencies
```

## Requirements

- Python 3.8+
- Gemini API key
- Dependencies listed in requirements.txt

## Development

The system uses:
- **LangGraph** for agent orchestration
- **LangChain** for tool integration
- **Google Gemini** for LLM capabilities
- **Rich** for CLI formatting

## License

MIT License 