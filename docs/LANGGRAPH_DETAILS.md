# LangGraph Implementation Details

## Understanding LangGraph in Our System

This document provides deep insights into how LangGraph orchestrates our multi-agent system.

## Core LangGraph Concepts

### 1. **StateGraph**
The foundation of our workflow - manages state transitions between nodes.

```python
from langgraph.graph import StateGraph, START, END

# Our state definition
class GraphState(TypedDict):
    messages: List[BaseMessage]      # Conversation messages
    query: str                       # Current query
    route: Literal["general", "research"]  # Routing decision
    routing_reasoning: str           # Why this route was chosen
    response: str                    # Final response
    steps: List[Dict[str, Any]]     # Tools used
    error: str                       # Any errors
    conversation_history: List[ConversationEntry]  # Full history
```

### 2. **Nodes**
Functions that process and transform state.

```
┌─────────────────────────────────────────────────────┐
│                    NODES                             │
├─────────────────────────────────────────────────────┤
│ • supervisor_node - Makes routing decisions          │
│ • general_qa_node - Handles simple queries           │
│ • research_node - Conducts complex research          │
└─────────────────────────────────────────────────────┘
```

### 3. **Edges**
Define the flow between nodes.

```
┌─────────────────────────────────────────────────────┐
│                    EDGES                             │
├─────────────────────────────────────────────────────┤
│ • START → supervisor_node (always)                   │
│ • supervisor_node → conditional routing              │
│ • general_qa_node → END                              │
│ • research_node → END                                │
└─────────────────────────────────────────────────────┘
```

## LangGraph State Flow Visualization

```
                        START
                          │
                          ▼
                ┌─────────────────┐
                │ supervisor_node │
                │                 │
                │ • Adds message  │
                │ • Gets route    │
                │ • Sets reason   │
                └────────┬────────┘
                         │
              Conditional Edge
              (route_decision)
                         │
           ┌─────────────┴─────────────┐
           │                           │
     route="general"             route="research"
           │                           │
           ▼                           ▼
   ┌───────────────┐           ┌───────────────┐
   │ general_qa_   │           │ research_node │
   │ node          │           │               │
   │               │           │ • Plan steps  │
   │ • Run ReAct   │           │ • Execute     │
   │ • Use tools   │           │ • Synthesize  │
   └───────┬───────┘           └───────┬───────┘
           │                           │
           │                           │
           └─────────┬─────────────────┘
                     │
                     ▼
                    END
```

## State Transformation Through Nodes

### Initial State (START)
```python
{
    "messages": [],
    "query": "What's the capital of France?",
    "route": "general",  # default
    "routing_reasoning": "",
    "response": "",
    "steps": [],
    "error": "",
    "conversation_history": [...]
}
```

### After supervisor_node
```python
{
    "messages": [HumanMessage("What's the capital of France?")],
    "query": "What's the capital of France?",
    "route": "general",  # ← Decided by supervisor
    "routing_reasoning": "Simple factual question...",  # ← Added
    "response": "",
    "steps": [],
    "error": "",
    "conversation_history": [...]
}
```

### After general_qa_node
```python
{
    "messages": [
        HumanMessage("What's the capital of France?"),
        AIMessage("Paris")  # ← Added
    ],
    "query": "What's the capital of France?",
    "route": "general",
    "routing_reasoning": "Simple factual question...",
    "response": "Paris",  # ← Added
    "steps": [  # ← Added
        {
            "tool": "web_search",
            "input": "capital of France",
            "output": "Paris is the capital..."
        }
    ],
    "error": "",
    "conversation_history": [...]
}
```

## LangGraph Workflow Building

### Code Structure in supervisor_graph.py

```python
def _build_graph(self):
    """Build the LangGraph workflow."""
    
    # 1. Define workflow with state type
    workflow = StateGraph(GraphState)
    
    # 2. Add nodes (functions that transform state)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("general_qa", general_qa_node)
    workflow.add_node("research", research_node)
    
    # 3. Add edges (define flow)
    workflow.add_edge(START, "supervisor")  # Always start here
    
    # 4. Add conditional edges
    workflow.add_conditional_edges(
        "supervisor",           # From node
        route_decision,         # Decision function
        {                      # Mapping of decisions to nodes
            "general": "general_qa",
            "research": "research"
        }
    )
    
    # 5. Add terminal edges
    workflow.add_edge("general_qa", END)
    workflow.add_edge("research", END)
    
    # 6. Compile into executable graph
    return workflow.compile()
```

## Deep Dive: Conditional Routing

### The route_decision Function
```python
def route_decision(state: GraphState) -> Literal["general", "research"]:
    """Route based on supervisor decision."""
    return state["route"]  # Simply returns the route set by supervisor
```

### Visual Representation
```
         state["route"] = ?
                │
      ┌─────────┴─────────┐
      │  route_decision   │
      └─────────┬─────────┘
                │
        ┌───────┴───────┐
        │               │
    "general"      "research"
        │               │
        ▼               ▼
  general_qa_node  research_node
```

## LangGraph Execution Model

### 1. **Graph Invocation**
```python
# In SupervisorGraph.query()
result = self.graph.invoke(initial_state)
```

### 2. **Execution Steps**
```
1. START
   ↓
2. Execute supervisor_node(state)
   → Updates state with route decision
   ↓
3. Evaluate conditional edge
   → route_decision(state) returns "general" or "research"
   ↓
4. Execute chosen node
   → general_qa_node(state) OR research_node(state)
   → Updates state with response
   ↓
5. END
   → Return final state
```

### 3. **State Persistence**
- Each node receives the FULL state
- Nodes return updated state (can modify any field)
- LangGraph merges updates automatically

## Advanced Features Used

### 1. **TypedDict State**
```python
class GraphState(TypedDict):
    # Provides type safety and IDE support
    # LangGraph knows exactly what fields exist
```

### 2. **Message History**
```python
from langgraph.graph.message import add_messages

# Messages accumulate through the workflow
# Each node can add to the message history
```

### 3. **Conditional Edges**
```python
workflow.add_conditional_edges(
    source_node,
    decision_function,  # Returns next node name
    routing_map        # Maps return values to nodes
)
```

## Benefits of LangGraph Architecture

### 1. **Clear Control Flow**
```
• Visual representation of agent coordination
• Easy to understand execution path
• Debuggable state transitions
```

### 2. **State Management**
```
• Centralized state definition
• Automatic state merging
• Type-safe operations
```

### 3. **Extensibility**
```
• Easy to add new nodes (agents)
• Simple to modify routing logic
• Can add complex conditional flows
```

## Execution Example

When user asks: "What's my name?" (with history showing "Hi, I'm Bob")

```
1. INVOKE
   graph.invoke({
     query: "What's my name?",
     conversation_history: [{query: "Hi, I'm Bob", ...}],
     ...
   })

2. SUPERVISOR_NODE
   → Sees query + history
   → Routes to "general"
   → Sets reasoning

3. ROUTE_DECISION
   → Returns "general"

4. GENERAL_QA_NODE
   → Receives full state including history
   → Builds context: "User: Hi, I'm Bob..."
   → Agent determines: "Your name is Bob"
   → Updates state with response

5. END
   → Returns complete state
   → Response extracted and shown to user
```

## State Flow Summary

```
┌────────────────────────────────────────┐
│           Initial State                 │
│  • Query from user                     │
│  • Conversation history                │
│  • Empty response                      │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│         Supervisor Node                 │
│  • Analyzes query + context           │
│  • Decides route                      │
│  • Adds reasoning                     │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│      Agent Node (General/Research)      │
│  • Executes with full context         │
│  • Uses tools as needed               │
│  • Generates response                 │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│           Final State                   │
│  • Complete message history           │
│  • Response ready                     │
│  • Execution steps logged             │
└────────────────────────────────────────┘
```

This architecture makes our multi-agent system robust, maintainable, and easy to extend! 