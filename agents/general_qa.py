"""General Q&A agent for simple queries."""

from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from llm.langchain_adapter import LangChainGeminiAdapter
from tools.repl_tool import CustomREPLTool
from tools.web_search_tool import WebSearchTool
from prompts.agent_prompts import REACT_AGENT_PROMPT
from .custom_parsers import RobustReActOutputParser


class GeneralQAAgent:
    """General Q&A agent with basic tools for simple queries."""
    
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
        self.tools = [
            CustomREPLTool(),
            WebSearchTool()
        ]
        
        # Create ReAct prompt template from prompts directory
        self.prompt_template = PromptTemplate.from_template(REACT_AGENT_PROMPT)
        
        # Create agent with custom output parser
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt_template,
            output_parser=RobustReActOutputParser()
        )
        
        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
    
    def answer(self, query: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Answer a query using available tools.
        
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
            
            # Combine context with query if available
            full_input = context_str + query if context else query
            
            # Execute the agent
            result = self.executor.invoke({
                "input": full_input
            })
            
            # Extract intermediate steps for transparency
            steps = []
            if "intermediate_steps" in result:
                for action, observation in result["intermediate_steps"]:
                    steps.append({
                        "tool": action.tool,
                        "input": action.tool_input,
                        "output": observation
                    })
            
            return {
                "answer": result.get("output", "I couldn't generate an answer."),
                "steps": steps,
                "success": True
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
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ] 