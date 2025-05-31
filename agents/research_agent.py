"""Deep research agent with planning and iteration capabilities."""

from typing import List, Dict, Any, Optional
from llm.langchain_adapter import LangChainGeminiAdapter
from tools.repl_tool import CustomREPLTool
from tools.web_search_tool import WebSearchTool
from tools.wikipedia_tool import WikipediaTool
from tools.arxiv_tool import ArxivTool
from prompts.research_prompts import (
    RESEARCH_PLANNING_PROMPT,
    RESEARCH_SYNTHESIS_PROMPT,
    RESEARCH_ITERATION_PROMPT
)
from prompts.schemas import RESEARCH_PLAN_SCHEMA


class ResearchAgent:
    """Research agent with planning, multiple tools, and iterative execution."""
    
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
        self.tools = {
            "wikipedia": WikipediaTool(),
            "arxiv": ArxivTool(),
            "web_search": WebSearchTool(),
            "python_repl": CustomREPLTool()
        }
        self.max_iterations = 5
    
    def create_research_plan(self, query: str, context: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Create a research plan for the given query."""
        # Build context string if available
        context_str = ""
        if context:
            context_str = "\n\nConversation History:\n"
            for entry in context[-3:]:  # Use last 3 interactions for context
                context_str += f"User: {entry['query']}\n"
                context_str += f"Assistant: {entry['response'][:100]}...\n\n"
        
        prompt = RESEARCH_PLANNING_PROMPT.format(query=context_str + query if context else query)
        
        # Get structured plan
        response = self.llm.get_structured_response(prompt, RESEARCH_PLAN_SCHEMA)
        
        if "error" in response:
            # Fallback plan if planning fails
            return [
                {
                    "step": 1,
                    "action": "Search for papers on systematic market making",
                    "tool": "arxiv",
                    "query": "market making execution systematic"
                },
                {
                    "step": 2,
                    "action": "Search for order book datasets",
                    "tool": "web_search",
                    "query": "order book dataset download backtesting"
                }
            ]
        
        # Filter out steps with None queries or tools
        plan = response.get("plan", [])
        valid_plan = []
        for step in plan:
            if step.get("tool") and step.get("query"):
                valid_plan.append(step)
            elif step.get("tool") == "arxiv" and not step.get("query"):
                # For arxiv steps without queries, generate a basic query
                step["query"] = query  # Use the original query as fallback
                valid_plan.append(step)
            elif step.get("tool") == "web_search" and not step.get("query"):
                # For web search steps without queries, generate a basic query
                step["query"] = query  # Use the original query as fallback
                valid_plan.append(step)
        
        return valid_plan if valid_plan else [{
            "step": 1,
            "action": "Search for general information",
            "tool": "web_search",
            "query": query
        }]
    
    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single research step."""
        tool_name = step.get("tool")
        query = step.get("query")
        
        if not tool_name or not query:
            return {
                "success": False,
                "error": f"Invalid step: missing tool or query",
                "output": ""
            }
        
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "output": ""
            }
        
        try:
            tool = self.tools[tool_name]
            result = tool._run(query)
            
            return {
                "success": True,
                "tool": tool_name,
                "query": query,
                "output": result
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_name,
                "query": query,
                "error": str(e),
                "output": f"Error using {tool_name}: {str(e)}"
            }
    
    def synthesize_findings(self, query: str, findings: List[Dict[str, Any]], context: Optional[List[Dict]] = None) -> str:
        """Synthesize all research findings into a comprehensive response."""
        # Build context string if available
        context_str = ""
        if context:
            context_str = "\n\nConversation History:\n"
            for entry in context[-3:]:  # Use last 3 interactions for context
                context_str += f"User: {entry['query']}\n"
                context_str += f"Assistant: {entry['response'][:100]}...\n\n"
            context_str += "Current Query:\n"
        
        # Format findings for synthesis
        findings_text = "\n\n".join([
            f"Step {i+1} - {f['tool']}:\n{f['output']}"
            for i, f in enumerate(findings)
            if f.get("success", False)
        ])
        
        prompt = RESEARCH_SYNTHESIS_PROMPT.format(
            query=context_str + query if context else query,
            findings=findings_text
        )
        
        return self.llm._call(prompt)
    
    def should_continue_research(
        self, 
        query: str, 
        completed_steps: List[Dict], 
        findings: List[Dict],
        remaining_plan: List[Dict],
        iteration: int
    ) -> bool:
        """Determine if more research is needed."""
        if iteration >= self.max_iterations:
            return False
        
        if not remaining_plan:
            return False
        
        # If we have at least 2 successful findings, we might have enough
        successful_findings = [f for f in findings if f.get("success")]
        if len(successful_findings) >= 2:
            # Ask LLM if we have enough information
            completed_desc = [f"{s['action']} using {s['tool']}" for s in completed_steps]
            findings_summary = [f"{f['tool']}: Found relevant information" for f in successful_findings]
            
            prompt = RESEARCH_ITERATION_PROMPT.format(
                query=query,
                completed_steps="\n".join(completed_desc),
                findings="\n".join(findings_summary),
                remaining_plan=f"{len(remaining_plan)} steps remaining"
            )
            
            response = self.llm._call(prompt)
            
            # Simple heuristic: continue if response suggests more research
            continue_keywords = ["continue", "proceed", "more research", "additional"]
            stop_keywords = ["sufficient", "enough", "synthesize", "conclude"]
            
            response_lower = response.lower()
            continue_score = sum(1 for kw in continue_keywords if kw in response_lower)
            stop_score = sum(1 for kw in stop_keywords if kw in response_lower)
            
            return continue_score > stop_score
        
        # If we have less than 2 findings, continue
        return True
    
    def research(self, query: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Conduct comprehensive research on the query.
        
        Args:
            query: The research query
            context: Optional conversation history
        
        Returns:
            Dict with 'answer', 'plan', 'findings', and 'success'
        """
        try:
            # Create research plan with context
            plan = self.create_research_plan(query, context)
            
            if not plan:
                return {
                    "answer": "I couldn't create a research plan for this query.",
                    "plan": [],
                    "findings": [],
                    "success": False
                }
            
            # Execute plan iteratively
            findings = []
            completed_steps = []
            iteration = 0
            
            for step in plan:
                # Check if we should continue
                if iteration > 0 and not self.should_continue_research(
                    query, 
                    completed_steps,
                    findings,
                    plan[len(completed_steps):],
                    iteration
                ):
                    break
                
                # Execute step
                result = self.execute_step(step)
                findings.append(result)
                completed_steps.append(step)
                iteration += 1
                
                # Stop if we hit max iterations
                if iteration >= self.max_iterations:
                    break
            
            # Synthesize findings with context
            answer = self.synthesize_findings(query, findings, context)
            
            return {
                "answer": answer,
                "plan": plan,
                "findings": findings,
                "completed_steps": len(completed_steps),
                "total_steps": len(plan),
                "success": True
            }
            
        except Exception as e:
            return {
                "answer": f"Research failed: {str(e)}",
                "plan": [],
                "findings": [],
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
            for name, tool in self.tools.items()
        ] 