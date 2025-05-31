"""Supervisor agent for routing requests to specialized agents."""

from typing import Dict, Any, List, Optional
from llm.langchain_adapter import LangChainGeminiAdapter
from prompts.supervisor_prompts import SUPERVISOR_ROUTING_PROMPT
from prompts.schemas import ROUTING_SCHEMA


class SupervisorAgent:
    """Supervisor agent that routes queries to appropriate specialized agents."""
    
    def __init__(self, llm: LangChainGeminiAdapter):
        self.llm = llm
    
    def route(self, query: str, context: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Analyze query and determine routing.
        
        Args:
            query: The user query
            context: Optional conversation history
        
        Returns:
            Dict with 'route' (either 'general' or 'research') and 'reasoning'
        """
        # Build context string if available
        context_str = ""
        if context:
            context_str = "\n\nConversation History:\n"
            for entry in context[-3:]:  # Use last 3 interactions for context
                context_str += f"User: {entry['query']}\n"
                context_str += f"Assistant ({entry['route']}): {entry['response'][:100]}...\n\n"
            context_str += "Current Query:\n"
        
        # Format the routing prompt with context
        full_query = context_str + query if context else query
        prompt = SUPERVISOR_ROUTING_PROMPT.format(query=full_query)
        
        # Get structured routing decision
        routing_decision = self.llm.get_structured_response(prompt, ROUTING_SCHEMA)
        
        # Validate response
        if "error" in routing_decision:
            # Default to general agent if there's an error
            return {
                "route": "general",
                "reasoning": f"Defaulting to general agent due to routing error: {routing_decision.get('error')}"
            }
        
        # Ensure valid route
        route = routing_decision.get("route", "general")
        if route not in ["general", "research"]:
            route = "general"
        
        return {
            "route": route,
            "reasoning": routing_decision.get("reasoning", "No reasoning provided")
        }
    
    def explain_routing(self, query: str) -> str:
        """Get a human-readable explanation of the routing decision."""
        decision = self.route(query)
        return (
            f"Query: {query}\n"
            f"Routed to: {decision['route']} agent\n"
            f"Reasoning: {decision['reasoning']}"
        ) 