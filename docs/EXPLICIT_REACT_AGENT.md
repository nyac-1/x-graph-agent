# Explicit React Agent Implementation

## Overview

This document explains the explicit implementation of the React (Reasoning and Acting) agent pattern, breaking down the Think-Act-Observe cycle into its core components.

## The React Pattern

The React pattern is a powerful approach for building agents that can reason about tasks and take actions using tools. The pattern consists of three main phases:

1. **Think**: The agent reasons about what it needs to do
2. **Act**: The agent decides which tool to use and with what input
3. **Observe**: The agent observes the output from the tool

This cycle repeats until the agent arrives at a final answer.

## Implementation Components

### 1. ExplicitReActAgent Class

The `ExplicitReActAgent` class is the core implementation that explicitly shows each phase of the React cycle.

```python
class ExplicitReActAgent:
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
        self.tools = {
            "web_search": WebSearchTool(),
            "python_repl": CustomREPLTool()
        }
        self.max_iterations = 5
        self.verbose = True
```

Key components:
- **LLM**: The language model that powers the reasoning
- **Tools**: Available actions the agent can take
- **Max Iterations**: Prevents infinite loops
- **Verbose Mode**: Shows the thinking process

### 2. The Think-Act-Observe Cycle

The main logic is in the `_think_act_observe` method:

```python
def _think_act_observe(self, query: str, context: str = "") -> Tuple[str, List[Dict]]:
    agent_scratchpad = ""
    steps = []
    
    for iteration in range(self.max_iterations):
        # THINK: Generate prompt and get LLM response
        prompt = REACT_AGENT_PROMPT.format(...)
        llm_output = self.llm.invoke(prompt).content
        
        # Parse the output
        parsed = self._parse_llm_output(llm_output)
        
        # Handle based on type
        if parsed["type"] == "final_answer":
            # Return the final answer
            return parsed["final_answer"], steps
            
        elif parsed["type"] == "action":
            # ACT: Execute the action
            # OBSERVE: Get the tool output
            observation = self._execute_tool(parsed["action"], parsed["action_input"])
            
            # Update scratchpad for next iteration
            agent_scratchpad += f"\nThought: {parsed['thought']}"
            agent_scratchpad += f"\nAction: {parsed['action']}"
            agent_scratchpad += f"\nAction Input: {parsed['action_input']}"
            agent_scratchpad += f"\nObservation: {observation}"
```

### 3. Output Parsing

The `_parse_llm_output` method extracts structured information from the LLM's response:

```python
def _parse_llm_output(self, output: str) -> Dict[str, Any]:
    # Extract Thought
    thought_match = re.search(r"Thought\s*:\s*(.+?)(?=\nAction|\nFinal Answer|\Z)", ...)
    
    # Check for Final Answer
    final_answer_match = re.search(r"Final Answer\s*:\s*(.+?)(?:\n|$)", ...)
    
    # Check for Action and Action Input
    action_match = re.search(r"Action\s*:\s*([^\n]+).*?Action\s*Input\s*:\s*(.+?)", ...)
```

This parsing is crucial for understanding what the LLM wants to do next.

### 4. Tool Execution

The `_execute_tool` method handles the actual execution of tools:

```python
def _execute_tool(self, tool_name: str, tool_input: str) -> str:
    tool_name = tool_name.lower().replace(" ", "_")
    
    if tool_name in self.tools:
        try:
            result = self.tools[tool_name].run(tool_input)
            return str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"
```

## The Agent Scratchpad

The agent scratchpad is a crucial component that maintains the conversation history within each query:

```
Thought: I need to search for current weather information
Action: web_search
Action Input: weather today New York
Observation: Current weather in New York is 72°F with partly cloudy skies
Thought: Based on the search results, I can provide the weather information
Final Answer: The weather in New York today is 72°F with partly cloudy skies.
```

This scratchpad is appended to the prompt in each iteration, allowing the LLM to see its previous thoughts and observations.

## Integration with GeneralQAAgent

The `GeneralQAAgent` class wraps the explicit React implementation to maintain compatibility with the existing system:

```python
class GeneralQAAgent:
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
        self.react_agent = ExplicitReActAgent(llm)
    
    def answer(self, query: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        # Execute the Think-Act-Observe cycle
        answer, steps = self.react_agent._think_act_observe(query, context_str)
        
        # Return in expected format
        return {
            "answer": answer,
            "steps": formatted_steps,
            "success": True,
            "detailed_steps": steps  # Include detailed steps for transparency
        }
```

## Example Flow

Here's a visualization of how a query flows through the system:

```
User Query: "What is the weather in Tokyo?"
    |
    v
ITERATION 1:
  THINK: "I need to search for current weather information in Tokyo"
  ACT: Tool = web_search, Input = "weather today Tokyo Japan"
  OBSERVE: "Current weather in Tokyo: 68°F, cloudy with chance of rain"
    |
    v
ITERATION 2:
  THINK: "I now have the weather information for Tokyo"
  FINAL ANSWER: "The weather in Tokyo is currently 68°F and cloudy with a chance of rain."
```

## Benefits of Explicit Implementation

1. **Transparency**: Every step of the reasoning process is visible
2. **Debugging**: Easy to see where the agent might be going wrong
3. **Control**: Fine-grained control over each phase
4. **Learning**: Helps understand how React agents work internally
5. **Customization**: Easy to modify behavior at each step

## Comparison with LangChain's create_react_agent

The explicit implementation replaces:
```python
# LangChain approach
self.agent = create_react_agent(llm, tools, prompt, output_parser)
self.executor = AgentExecutor(agent, tools, ...)
```

With our explicit approach that shows:
- How prompts are constructed
- How outputs are parsed
- How the iteration loop works
- How tools are executed
- How the scratchpad is maintained

This makes the "magic" of React agents visible and understandable. 