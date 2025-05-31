# Multi-Agent System Workflow & Architecture

## Overview

This document provides a comprehensive visual guide to how user queries flow through the multi-agent system, with special focus on the `graph/` and `agents/` directories.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              USER                                    │
│                           (main.py CLI)                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUPERVISOR GRAPH                                  │
│                 (graph/supervisor_graph.py)                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  SupervisorGraph Class                                       │   │
│  │  • Maintains conversation_history: List[ConversationEntry]   │   │
│  │  • Creates and manages all agents                            │   │
│  │  • Builds LangGraph workflow                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENTS                                       │
│                    (agents/ directory)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │  Supervisor  │  │ General Q&A  │  │     Research Agent     │   │
│  │   Agent      │  │    Agent     │  │                        │   │
│  └──────────────┘  └──────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Detailed Query Flow

### 1. Query Entry & State Initialization

```
USER INPUT: "What's my name?"
     │
     ▼
[main.py] → run_query(graph, query)
     │
     ▼
[supervisor_graph.py] → SupervisorGraph.query()
     │
     ▼
Creates Initial GraphState:
┌─────────────────────────────────────┐
│ GraphState {                        │
│   messages: [],                     │
│   query: "What's my name?",        │
│   route: "general",                 │
│   routing_reasoning: "",            │
│   response: "",                     │
│   steps: [],                        │
│   error: "",                        │
│   conversation_history: [           │
│     {                               │
│       timestamp: "14:23:15",        │
│       query: "Hi, I'm John",        │
│       response: "Hello John!",      │
│       route: "general",             │
│       reasoning: "..."              │
│     }                               │
│   ]                                 │
│ }                                   │
└─────────────────────────────────────┘
```

### 2. Supervisor Node (Routing Decision)

```
                    GraphState
                        │
                        ▼
            ┌───────────────────────┐
            │   SUPERVISOR NODE     │
            │ (supervisor_node func) │
            └───────────────────────┘
                        │
                        ▼
            ┌───────────────────────────────────┐
            │ agents/supervisor.py              │
            │                                   │
            │ SupervisorAgent.route(           │
            │   query="What's my name?",       │
            │   context=[                      │
            │     {query: "Hi, I'm John",      │
            │      response: "Hello John!"...} │
            │   ]                              │
            │ )                                │
            └───────────────────────────────────┘
                        │
                        ▼
            Builds context string:
            ┌─────────────────────────────────────┐
            │ "Conversation History:              │
            │  User: Hi, I'm John                 │
            │  Assistant (general): Hello John!.. │
            │                                     │
            │  Current Query:                     │
            │  What's my name?"                   │
            └─────────────────────────────────────┘
                        │
                        ▼
            Sends to LLM with SUPERVISOR_ROUTING_PROMPT
                        │
                        ▼
            Returns routing decision:
            ┌─────────────────────────────────────┐
            │ {                                   │
            │   route: "general",                 │
            │   reasoning: "Simple info retrieval │
            │              from conversation..."   │
            │ }                                   │
            └─────────────────────────────────────┘
```

### 3. Conditional Routing

```
        GraphState (with route="general")
                    │
                    ▼
        ┌─────────────────────────┐
        │  CONDITIONAL EDGES      │
        │  route_decision()       │
        └─────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
    "general"               "research"
        │                       │
        ▼                       ▼
┌──────────────┐       ┌──────────────┐
│ general_qa_  │       │ research_    │
│ node         │       │ node         │
└──────────────┘       └──────────────┘
```

### 4. General Q&A Node Execution

```
                GraphState
                    │
                    ▼
        ┌───────────────────────┐
        │   GENERAL Q&A NODE    │
        │ (general_qa_node func)│
        └───────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────────┐
    │ agents/general_qa.py                    │
    │                                         │
    │ GeneralQAAgent.answer(                  │
    │   query="What's my name?",             │
    │   context=[                            │
    │     {                                  │
    │       query: "Hi, I'm John",           │
    │       response: "Hello John!",         │
    │       route: "general",                │
    │       ...                              │
    │     }                                  │
    │   ]                                    │
    │ )                                      │
    └─────────────────────────────────────────┘
                    │
                    ▼
        Builds context for ReAct agent:
        ┌─────────────────────────────────────┐
        │ "Conversation History:              │
        │  User: Hi, I'm John                 │
        │  Assistant: Hello John!             │
        │                                     │
        │  Current Query:                     │
        │  What's my name?"                   │
        └─────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────┐
        │        ReAct Agent Chain            │
        │                                     │
        │  Available Tools:                   │
        │  • python_repl (CustomREPLTool)     │
        │  • web_search (WebSearchTool)       │
        │                                     │
        │  Thought: Context shows user is John│
        │  Final Answer: Your name is John    │
        └─────────────────────────────────────┘
                    │
                    ▼
            Returns result:
            {
              answer: "Your name is John",
              steps: [],
              success: true
            }
```

### 5. State Update & History Recording

```
        Result from agent
                │
                ▼
    Updates GraphState:
    ┌─────────────────────────────────────┐
    │ GraphState {                        │
    │   ...                               │
    │   response: "Your name is John",    │
    │   steps: [],                        │
    │   messages: [                       │
    │     HumanMessage("What's my name?"),│
    │     AIMessage("Your name is John")  │
    │   ]                                 │
    │ }                                   │
    └─────────────────────────────────────┘
                │
                ▼
    ┌─────────────────────────────────────┐
    │      END Node → Return to           │
    │      SupervisorGraph.query()        │
    └─────────────────────────────────────┘
                │
                ▼
    Appends to conversation_history:
    ┌─────────────────────────────────────┐
    │ conversation_history.append({       │
    │   timestamp: "14:23:45",            │
    │   query: "What's my name?",         │
    │   response: "Your name is John",    │
    │   route: "general",                 │
    │   routing_reasoning: "Simple..."     │
    │ })                                  │
    └─────────────────────────────────────┘
```

## Context Management Flow

### Context Flow Through the System:

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT LIFECYCLE                         │
└─────────────────────────────────────────────────────────────┘

1. Storage in SupervisorGraph
   └─> self.conversation_history: List[ConversationEntry]

2. Passed to GraphState
   └─> state["conversation_history"] = self.conversation_history

3. Supervisor Routing Context
   └─> SupervisorAgent.route(query, context=history[-3:])
       └─> Includes in routing prompt

4. Agent Execution Context
   └─> GeneralQAAgent.answer(query, context=history[-5:])
   └─> ResearchAgent.research(query, context=history[-3:])
       └─> Prepended to agent prompts

5. Post-execution Update
   └─> New entry added to conversation_history
   └─> Available for next query
```

## Research Agent Flow (Alternative Path)

When supervisor routes to "research":

```
                GraphState
                    │
                    ▼
        ┌───────────────────────┐
        │    RESEARCH NODE      │
        │ (research_node func)  │
        └───────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────────┐
    │ agents/research_agent.py                │
    │                                         │
    │ ResearchAgent.research(                 │
    │   query="Explain quantum computing",    │
    │   context=[...conversation_history]     │
    │ )                                       │
    └─────────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────┐
        │   1. CREATE RESEARCH PLAN       │
        │   create_research_plan()        │
        │   → Uses context in planning    │
        └─────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────┐
        │   2. EXECUTE PLAN STEPS         │
        │   for step in plan:             │
        │     execute_step(step)          │
        │                                 │
        │   Tools:                        │
        │   • wikipedia                   │
        │   • arxiv                       │
        │   • web_search                  │
        │   • python_repl                 │
        └─────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────┐
        │   3. SYNTHESIZE FINDINGS        │
        │   synthesize_findings()         │
        │   → Uses context + findings     │
        └─────────────────────────────────┘
```

## Directory Structure & Connections

```
x-graph-agent/
│
├── main.py
│   └─> Entry point
│       └─> Creates SupervisorGraph
│       └─> Handles CLI commands (history, clear, exit)
│
├── graph/
│   └── supervisor_graph.py
│       ├─> SupervisorGraph class (stateful)
│       │   ├─> conversation_history: List[ConversationEntry]
│       │   ├─> llm: LangChainGeminiAdapter
│       │   ├─> supervisor: SupervisorAgent
│       │   ├─> general_agent: GeneralQAAgent
│       │   └─> research_agent: ResearchAgent
│       │
│       └─> LangGraph workflow definition
│           ├─> supervisor_node → routes queries
│           ├─> general_qa_node → simple queries
│           ├─> research_node → complex queries
│           └─> Conditional edges based on routing
│
├── agents/
│   ├── supervisor.py
│   │   └─> SupervisorAgent
│   │       └─> route(query, context) → decides agent
│   │
│   ├── general_qa.py
│   │   └─> GeneralQAAgent
│   │       └─> answer(query, context) → ReAct chain
│   │
│   └── research_agent.py
│       └─> ResearchAgent
│           ├─> research(query, context)
│           ├─> create_research_plan(query, context)
│           ├─> execute_step(step)
│           └─> synthesize_findings(query, findings, context)
│
└── llm/
    └── langchain_adapter.py
        └─> LangChainGeminiAdapter
            └─> Wraps CustomGeminiLLM for LangChain
```

## Complete Query Lifecycle

```
1. USER INPUT
   │
   ├─> "Hi, I'm Alice" ──────────┐
   │                             │
   ├─> "What is 2+2?" ───────────┤
   │                             │
   └─> "What's my name?" ────────┤
                                 │
2. SUPERVISOR GRAPH              │
   │                             │
   ├─> Query 1: Routes to general, no context
   │   └─> Response: "Hello Alice!"
   │   └─> Saves to history
   │                             │
   ├─> Query 2: Routes to general with context
   │   └─> Context: [Query 1 history]
   │   └─> Response: "4"
   │   └─> Saves to history
   │                             │
   └─> Query 3: Routes to general with context
       └─> Context: [Query 1 & 2 history]
       └─> Agent sees: "User: Hi, I'm Alice"
       └─> Response: "Your name is Alice"
       └─> Saves to history

3. SESSION STATE
   conversation_history = [
     {timestamp: "14:20:00", query: "Hi, I'm Alice", ...},
     {timestamp: "14:20:30", query: "What is 2+2?", ...},
     {timestamp: "14:21:00", query: "What's my name?", ...}
   ]
```

## Key Components Interaction

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Conversation   │────▶│   Supervisor    │────▶│     Agent       │
│    History      │     │   (Router)      │     │  (Executor)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                        │
        │                       │                        │
        ▼                       ▼                        ▼
  Maintains state         Uses context for         Uses context for
  across queries          routing decision         better answers
```

## Summary

The multi-agent system creates a seamless conversational experience by:

1. **Maintaining State**: SupervisorGraph holds conversation history
2. **Smart Routing**: Supervisor uses context to route queries
3. **Context-Aware Agents**: Each agent receives relevant history
4. **Continuous Learning**: Each interaction enriches future responses

This architecture ensures that agents can reference previous interactions, making the system feel more natural and intelligent. 