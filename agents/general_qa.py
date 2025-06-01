"""General Q&A agent for simple queries."""

from typing import List, Dict, Any, Optional, Tuple
import re
from llm.langchain_adapter import LangChainGeminiAdapter
from tools.repl_tool import CustomREPLTool
from tools.web_search_tool import WebSearchTool
from prompts.agent_prompts import REACT_AGENT_PROMPT


class ExplicitReActAgent:
    """Explicit implementation of ReAct pattern showing Think-Act-Observe cycle."""
    
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
        self.tools = {
            "web_search": WebSearchTool(),
            "python_repl": CustomREPLTool()
        }
        self.max_iterations = 5
        self.verbose = True
    
    def _parse_llm_output(self, output: str) -> Dict[str, Any]:
        """
        Parse LLM output to extract thought, action, action input, or final answer.
        
        Returns:
            Dict with keys: type ('action' or 'final_answer'), content
        """
        output = output.strip()
        
        # Check for Final Answer
        final_answer_match = re.search(
            r"Final Answer\s*:\s*(.+?)(?:\n|$)", 
            output, 
            re.IGNORECASE | re.DOTALL
        )
        
        # Check for Action and Action Input
        action_match = re.search(
            r"Action\s*:\s*([^\n]+).*?Action\s*Input\s*:\s*(.+?)(?=\nObservation|\nThought|\nFinal Answer|\Z)", 
            output, 
            re.DOTALL | re.IGNORECASE
        )
        
        # Extract Thought
        thought_match = re.search(
            r"Thought\s*:\s*(.+?)(?=\nAction|\nFinal Answer|\Z)",
            output,
            re.DOTALL | re.IGNORECASE
        )
        
        thought = thought_match.group(1).strip() if thought_match else ""
        
        # If both action and final answer are present, prioritize based on position
        if action_match and final_answer_match:
            action_pos = action_match.start()
            final_pos = final_answer_match.start()
            
            # If action comes first, it's likely the LLM included observation/final answer incorrectly
            if action_pos < final_pos:
                return {
                    "type": "action",
                    "thought": thought,
                    "action": action_match.group(1).strip(),
                    "action_input": action_match.group(2).strip()
                }
        
        # Normal priority: final answer first, then action
        if final_answer_match:
            return {
                "type": "final_answer",
                "thought": thought,
                "final_answer": final_answer_match.group(1).strip()
            }
        elif action_match:
            return {
                "type": "action",
                "thought": thought,
                "action": action_match.group(1).strip(),
                "action_input": action_match.group(2).strip()
            }
        else:
            # If we can't parse, return as error
            return {
                "type": "error",
                "thought": thought,
                "error": "Could not parse LLM output"
            }
    
    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute a tool and return the observation."""
        # Normalize tool name
        tool_name = tool_name.lower().replace(" ", "_")
        
        if tool_name in self.tools:
            try:
                result = self.tools[tool_name].run(tool_input)
                return str(result)
            except Exception as e:
                return f"Error executing tool: {str(e)}"
        else:
            return f"Unknown tool: {tool_name}. Available tools: {list(self.tools.keys())}"
    
    def _think_act_observe(self, query: str, context: str = "") -> Tuple[str, List[Dict]]:
        """
        Execute the Think-Act-Observe cycle.
        
        Returns:
            Tuple of (final_answer, steps_taken)
        """
        # Initialize agent scratchpad
        agent_scratchpad = ""
        steps = []
        
        # Build initial prompt
        tool_descriptions = "\n".join([
            f"{name}: {tool.description}"
            for name, tool in self.tools.items()
        ])
        tool_names = ", ".join(self.tools.keys())
        
        for iteration in range(self.max_iterations):
            # THINK: Generate prompt and get LLM response
            prompt = REACT_AGENT_PROMPT.format(
                input=query,
                tools=tool_descriptions,
                tool_names=tool_names,
                agent_scratchpad=agent_scratchpad
            )
            
            if context:
                prompt = context + "\n\n" + prompt
            
            if self.verbose:
                print(f"\n--- Iteration {iteration + 1} ---")
                print("THINKING...")
            
            # Get LLM response
            llm_output = self.llm.invoke(prompt)
            
            # Handle both string and object responses
            if hasattr(llm_output, 'content'):
                llm_output = llm_output.content
            else:
                llm_output = str(llm_output)
            
            if self.verbose:
                print(f"LLM Output:\n{llm_output}")
            
            # Parse the output
            parsed = self._parse_llm_output(llm_output)
            
            # Handle based on type
            if parsed["type"] == "final_answer":
                # We have our final answer
                if self.verbose:
                    print(f"\nFINAL ANSWER: {parsed['final_answer']}")
                
                steps.append({
                    "iteration": iteration + 1,
                    "thought": parsed["thought"],
                    "type": "final_answer",
                    "content": parsed["final_answer"]
                })
                
                return parsed["final_answer"], steps
            
            elif parsed["type"] == "action":
                # ACT: Execute the action
                if self.verbose:
                    print(f"\nACTION: {parsed['action']}")
                    print(f"ACTION INPUT: {parsed['action_input']}")
                
                # OBSERVE: Get the tool output
                observation = self._execute_tool(parsed["action"], parsed["action_input"])
                
                if self.verbose:
                    print(f"OBSERVATION: {observation}")
                
                # Record the step
                steps.append({
                    "iteration": iteration + 1,
                    "thought": parsed["thought"],
                    "type": "action",
                    "tool": parsed["action"],
                    "tool_input": parsed["action_input"],
                    "observation": observation
                })
                
                # Update agent scratchpad for next iteration
                agent_scratchpad += f"\nThought: {parsed['thought']}"
                agent_scratchpad += f"\nAction: {parsed['action']}"
                agent_scratchpad += f"\nAction Input: {parsed['action_input']}"
                agent_scratchpad += f"\nObservation: {observation}"
                agent_scratchpad += "\nThought: "
            
            else:
                # Error in parsing
                if self.verbose:
                    print(f"\nERROR: {parsed.get('error', 'Unknown error')}")
                
                steps.append({
                    "iteration": iteration + 1,
                    "type": "error",
                    "error": parsed.get('error', 'Unknown error')
                })
                
                # Try to recover by asking for proper format
                agent_scratchpad += "\nI need to follow the proper format. Let me try again.\nThought: "
        
        # Max iterations reached
        return "I couldn't find a satisfactory answer within the iteration limit.", steps


class GeneralQAAgent:
    """General Q&A agent with explicit Think-Act-Observe implementation."""
    
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
        self.react_agent = ExplicitReActAgent(llm)
    
    def answer(self, query: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Answer a query using explicit Think-Act-Observe cycle.
        
        Args:
            query: The user's question
            context: Optional conversation history
            
        Returns:
            Dict with 'answer' and 'steps' taken
        """
        try:
            # Build context string if conversation history is provided
            context_str = ""
            if context:
                context_str = "\nConversation History:\n"
                for entry in context[-5:]:  # Use last 5 interactions for context
                    context_str += f"User: {entry['query']}\n"
                    context_str += f"Assistant: {entry['response']}\n\n"
                context_str += "Current Query:\n"
            
            # Execute the Think-Act-Observe cycle
            answer, steps = self.react_agent._think_act_observe(query, context_str)
            
            # Format steps for output
            formatted_steps = []
            for step in steps:
                if step["type"] == "action":
                    formatted_steps.append({
                        "tool": step["tool"],
                        "input": step["tool_input"],
                        "output": step["observation"]
                    })
            
            return {
                "answer": answer,
                "steps": formatted_steps,
                "success": True,
                "detailed_steps": steps  # Include detailed steps for transparency
            }
            
        except Exception as e:
            return {
                "answer": f"I encountered an error: {str(e)}",
                "steps": [],
                "success": False,
                "error": str(e)
            }
    
    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """Get descriptions of available tools."""
        return [
            {
                "name": name,
                "description": tool.description
            }
            for name, tool in self.react_agent.tools.items()
        ] 