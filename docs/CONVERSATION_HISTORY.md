# Conversation History Feature

## Overview

The multi-agent system maintains conversation history throughout each session, allowing agents to reference previous interactions and provide contextual responses.

## Key Features

### 1. **Stateful Conversations**
- History is maintained at the supervisor level
- Each interaction is stored with timestamp, query, response, route, and reasoning
- Agents can access previous interactions when processing new queries

### 2. **Context-Aware Routing**
- Supervisor considers conversation history when routing queries
- Better decisions based on what was discussed previously

### 3. **Agent Memory**
- General Q&A agent uses last 5 interactions for context
- Research agent uses last 3 interactions for planning and synthesis
- Agents can reference information from previous queries

## Example Usage

```
User: Hi, my name is Alice and I'm researching quantum computing
Assistant: Hello Alice, nice to meet you!

User: What is 10 + 20?
Assistant: 30

User: What's my research topic?
Assistant: Based on our conversation, you're researching quantum computing.
```

## How It Works

### 1. **Storage**
```python
class ConversationEntry(TypedDict):
    timestamp: str
    query: str
    response: str
    route: str
    routing_reasoning: str
```

### 2. **Context Building**
Each agent builds context from history:
```python
context_str = "\nConversation History:\n"
for entry in context[-5:]:  # Last 5 interactions
    context_str += f"User: {entry['query']}\n"
    context_str += f"Assistant: {entry['response']}\n\n"
```

### 3. **Integration**
- Supervisor passes history to routing decisions
- Agents receive history in their answer/research methods
- Context is included in prompts sent to the LLM

## Commands

- `history` - Display full conversation history
- `clear` - Clear conversation history
- Session summary shown on exit

## Design Principles

1. **In-Memory Only**: History exists only during the session (stateless design)
2. **Limited Context**: Only recent interactions used to avoid prompt overflow
3. **Transparent**: Users can view history anytime
4. **Privacy**: No persistence between sessions

## Benefits

- Natural conversations with context retention
- Agents can provide more relevant responses
- Better routing decisions based on conversation flow
- Users don't need to repeat information 