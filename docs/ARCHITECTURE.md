# Architecture Overview

## System Design

The Multi-Agent System uses LangGraph to orchestrate three specialized agents:

### 1. Supervisor Agent (Router)
- **Purpose**: Analyzes incoming queries and routes them to the appropriate agent
- **Decision Criteria**:
  - Query complexity
  - Information needs
  - Required tools
- **Implementation**: `agents/supervisor.py`

### 2. General Q&A Agent
- **Purpose**: Handles straightforward queries requiring quick responses
- **Tools**:
  - Python REPL for calculations
  - Web Search for current information
- **Use Cases**:
  - Mathematical calculations
  - Simple factual questions
  - Current events lookup
- **Implementation**: `agents/general_qa.py`

### 3. Research Agent
- **Purpose**: Conducts in-depth research with planning and synthesis
- **Tools**:
  - Wikipedia for encyclopedic knowledge
  - ArXiv for academic papers
  - Web Search for current information
  - Python REPL for data analysis
- **Features**:
  - Multi-step planning
  - Iterative execution
  - Result synthesis
- **Implementation**: `agents/research_agent.py`

## LangGraph Flow

### Main Supervisor Graph
```python
START → Supervisor → Route Decision → [General Q&A | Research] → END
```

### Research Planning Graph
```python
START → Planner → Executor → [Continue/Synthesize] → END
                     ↑______________|
```

## State Management

### Supervisor Graph State
- `messages`: Conversation history
- `query`: Current user query
- `route`: Chosen agent route
- `response`: Final response
- `steps`: Execution steps
- `error`: Any errors encountered

### Research Graph State
- `plan`: Research plan steps
- `executed_steps`: Completed steps
- `findings`: Research results
- `iteration`: Current iteration
- `should_continue`: Continue flag

## Tool Integration

All tools extend LangChain's `BaseTool`:
- Consistent interface
- Error handling
- Async support
- Schema validation

## LLM Integration

The `CustomGeminiLLM` is wrapped with `LangChainGeminiAdapter`:
- Maintains the 3-method interface
- Compatible with LangChain agents
- Rate limiting (1s between calls)

## Key Design Decisions

1. **Modular Architecture**: Each agent is independent and can be modified without affecting others
2. **Tool Abstraction**: Tools are wrapped for consistent interface
3. **State-Based Flow**: LangGraph states enable complex workflows
4. **Error Resilience**: Graceful fallbacks at each level
5. **Extensibility**: Easy to add new agents or tools 