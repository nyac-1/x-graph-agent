"""Agent-specific prompts for multi-agent system."""

REACT_AGENT_PROMPT = """Answer the following question using the available tools when helpful.

Question: {input}

You have access to the following tools:
{tools}

IMPORTANT: You must follow this EXACT format. Do not deviate!

Use the following format:
Thought: Consider what information or calculation is needed
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original question

Rules:
1. NEVER output both an Action and Final Answer in the same response
2. If you need to use a tool, output ONLY Thought, Action, and Action Input
3. Wait for the Observation before providing Final Answer
4. When you have the result, output ONLY Thought and Final Answer

Begin!

Question: {input}
Thought: {agent_scratchpad}""" 