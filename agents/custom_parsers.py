"""Custom output parsers for agents."""

import re
from typing import Union
from langchain.agents.agent import AgentAction, AgentFinish
from langchain.agents.output_parsers.react_single_input import ReActSingleInputOutputParser


class RobustReActOutputParser(ReActSingleInputOutputParser):
    """A more robust ReAct output parser that handles common formatting issues."""
    
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        """Parse the output, handling cases where both action and final answer appear."""
        
        # Clean the text
        text = text.strip()
        
        # First priority: Check if this contains "Final Answer:" 
        # This is the definitive end of the agent's reasoning
        final_answer_match = re.search(
            r"Final Answer\s*:\s*(.+?)(?:\n|$)", 
            text, 
            re.IGNORECASE
        )
        
        # Check for action
        action_match = re.search(
            r"Action\s*:\s*([^\n]+).*?Action\s*Input\s*:\s*(.+?)(?=\nObservation|\nThought|\Z)", 
            text, 
            re.DOTALL | re.IGNORECASE
        )
        
        # Special case: If we see "I now know the final answer" followed by "Final Answer:", 
        # this is definitely a final answer, not an action
        knows_answer = re.search(
            r"Thought\s*:\s*I\s+(?:now\s+)?know\s+the\s+(?:final\s+)?answer",
            text,
            re.IGNORECASE
        )
        
        # If we have "I know the answer" and a final answer, return the final answer
        if knows_answer and final_answer_match:
            return AgentFinish(
                return_values={"output": final_answer_match.group(1).strip()},
                log=text
            )
        
        # If we have both action and final answer, check context
        if action_match and final_answer_match:
            # If the text contains "Observation:" it means we're looking at a full trace
            # In this case, prioritize Final Answer
            if "Observation:" in text:
                return AgentFinish(
                    return_values={"output": final_answer_match.group(1).strip()},
                    log=text
                )
            
            # Otherwise, check positions
            action_pos = action_match.start()
            final_pos = final_answer_match.start()
            
            if action_pos < final_pos:
                # Action comes first, return action
                action = action_match.group(1).strip()
                action_input = action_match.group(2).strip()
                return AgentAction(tool=action, tool_input=action_input, log=text)
            else:
                # Final answer comes first or same position, return final answer
                return AgentFinish(
                    return_values={"output": final_answer_match.group(1).strip()},
                    log=text
                )
        
        # If only final answer is present
        elif final_answer_match and not action_match:
            return AgentFinish(
                return_values={"output": final_answer_match.group(1).strip()},
                log=text
            )
        
        # If only action is present
        elif action_match and not final_answer_match:
            action = action_match.group(1).strip()
            action_input = action_match.group(2).strip()
            return AgentAction(tool=action, tool_input=action_input, log=text)
        
        # Last resort - try the parent parser
        try:
            return super().parse(text)
        except Exception:
            # If all else fails, check if this looks like a final answer without the format
            if knows_answer:
                # Try to extract answer after "I know the answer"
                answer_text = text.split("know the")[-1].split("answer")[-1].strip()
                if answer_text:
                    return AgentFinish(
                        return_values={"output": answer_text},
                        log=text
                    )
            
            # Really can't parse - return as exception
            return AgentAction(
                tool="_Exception",
                tool_input="Could not parse LLM output",
                log=text
            ) 