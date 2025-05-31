# Documentation Index

Welcome to the Multi-Agent System documentation! This directory contains comprehensive guides to understanding and working with the system.

## Core Documentation

### 1. **[System Workflow & Architecture](SYSTEM_WORKFLOW.md)** 
Comprehensive visual guide showing:
- Complete query flow from user input to response
- How context is managed throughout the system
- Detailed interaction between `graph/` and `agents/` directories
- State transformations at each step
- Visual diagrams and flowcharts

### 2. **[LangGraph Implementation Details](LANGGRAPH_DETAILS.md)**
Deep technical dive into:
- LangGraph concepts (StateGraph, Nodes, Edges)
- How our workflow is built and executed
- State management and transformations
- Conditional routing mechanisms
- Execution model and examples

### 3. **[Conversation History Feature](CONVERSATION_HISTORY.md)**
Understanding context management:
- How conversation history is stored
- Context flow through agents
- Memory limitations and design principles
- Usage examples and benefits

### 4. **[Architecture Overview](ARCHITECTURE.md)**
High-level system design:
- Component overview
- Agent capabilities
- Tool integration
- System boundaries

## Quick Reference

### Query Flow Summary
```
User → CLI → SupervisorGraph → Supervisor Agent → Route Decision
                                      ↓
                            General Q&A or Research Agent
                                      ↓
                               Tool Execution
                                      ↓
                              Response Generation
                                      ↓
                            Update Conversation History
                                      ↓
                                  User Gets Response
```

### Key Components
- **`main.py`** - CLI entry point
- **`graph/supervisor_graph.py`** - Orchestration and state management
- **`agents/`** - Agent implementations (Supervisor, General Q&A, Research)
- **`tools/`** - Tool wrappers (REPL, Web Search, Wikipedia, ArXiv)
- **`prompts/`** - All system prompts
- **`llm/`** - LLM integration layer

## Getting Started

1. Read [System Workflow](SYSTEM_WORKFLOW.md) for a complete understanding
2. Explore [LangGraph Details](LANGGRAPH_DETAILS.md) for technical implementation
3. Check [Conversation History](CONVERSATION_HISTORY.md) for context features
4. Review [Architecture](ARCHITECTURE.md) for system design

## Tips

- The visual diagrams in [System Workflow](SYSTEM_WORKFLOW.md) are the best way to understand the system
- [LangGraph Details](LANGGRAPH_DETAILS.md) explains the "why" behind our implementation choices
- All agents are context-aware thanks to the conversation history system 