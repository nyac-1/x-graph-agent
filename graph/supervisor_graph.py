"""Main supervisor routing graph using LangGraph."""

from typing import Dict, Any, List, Literal, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from llm.langchain_adapter import LangChainGeminiAdapter
from agents.supervisor import SupervisorAgent
from agents.general_qa import GeneralQAAgent
from agents.research_agent import ResearchAgent
import os
from dotenv import load_dotenv


class ConversationEntry(TypedDict):
    """Single conversation entry."""
    timestamp: str
    query: str
    response: str
    route: str
    routing_reasoning: str


class GraphState(TypedDict):
    """State for the supervisor graph."""
    messages: List[BaseMessage]
    query: str
    route: Literal["general", "research"]
    routing_reasoning: str
    response: str
    steps: List[Dict[str, Any]]
    error: str
    conversation_history: List[ConversationEntry]


class SupervisorGraph:
    """Stateful supervisor graph with conversation history."""
    
    def __init__(self, api_key: str = None):
        """Initialize the supervisor graph with conversation history."""
        # Load API key
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("No API key provided and GEMINI_API_KEY not found in environment")
        
        # Initialize conversation history
        self.conversation_history: List[ConversationEntry] = []
        
        # Initialize LLM and agents
        self.llm = LangChainGeminiAdapter(api_key=api_key)
        self.supervisor = SupervisorAgent(self.llm)
        self.general_agent = GeneralQAAgent(self.llm)
        self.research_agent = ResearchAgent(self.llm)
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Define graph nodes
        def supervisor_node(state: GraphState) -> GraphState:
            """Supervisor node that routes queries."""
            query = state["query"]
            messages = state.get("messages", [])
            
            # Add user message if not already present
            if not messages or messages[-1].content != query:
                messages.append(HumanMessage(content=query))
            
            # Get routing decision with conversation history
            routing = self.supervisor.route(query, context=self.conversation_history)
            
            return {
                **state,
                "messages": messages,
                "route": routing["route"],
                "routing_reasoning": routing["reasoning"],
                "conversation_history": self.conversation_history
            }
        
        def general_qa_node(state: GraphState) -> GraphState:
            """General Q&A agent node."""
            query = state["query"]
            conversation_history = state.get("conversation_history", [])
            
            # Execute general Q&A with conversation history
            result = self.general_agent.answer(query, context=conversation_history)
            
            # Update state
            messages = state.get("messages", [])
            messages.append(AIMessage(content=result["answer"]))
            
            return {
                **state,
                "messages": messages,
                "response": result["answer"],
                "steps": result.get("steps", []),
                "error": result.get("error", "")
            }
        
        def research_node(state: GraphState) -> GraphState:
            """Research agent node."""
            query = state["query"]
            conversation_history = state.get("conversation_history", [])
            
            # Execute research with conversation history
            result = self.research_agent.research(query, context=conversation_history)
            
            # Update state
            messages = state.get("messages", [])
            messages.append(AIMessage(content=result["answer"]))
            
            # Format steps from research findings
            steps = []
            for finding in result.get("findings", []):
                if finding.get("success"):
                    steps.append({
                        "tool": finding["tool"],
                        "input": finding["query"],
                        "output": finding["output"]
                    })
            
            return {
                **state,
                "messages": messages,
                "response": result["answer"],
                "steps": steps,
                "error": result.get("error", "")
            }
        
        def route_decision(state: GraphState) -> Literal["general", "research"]:
            """Route based on supervisor decision."""
            return state["route"]
        
        # Build the graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("general_qa", general_qa_node)
        workflow.add_node("research", research_node)
        
        # Add edges
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            route_decision,
            {
                "general": "general_qa",
                "research": "research"
            }
        )
        workflow.add_edge("general_qa", END)
        workflow.add_edge("research", END)
        
        # Compile the graph
        return workflow.compile()
    
    def query(self, query: str) -> Dict[str, Any]:
        """Run a query and update conversation history."""
        initial_state = {
            "messages": [],
            "query": query,
            "route": "general",  # Default
            "routing_reasoning": "",
            "response": "",
            "steps": [],
            "error": "",
            "conversation_history": self.conversation_history
        }
        
        result = self.graph.invoke(initial_state)
        
        # Add to conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "query": query,
            "response": result["response"],
            "route": result["route"],
            "routing_reasoning": result["routing_reasoning"]
        })
        
        return {
            "query": query,
            "route": result["route"],
            "routing_reasoning": result["routing_reasoning"],
            "response": result["response"],
            "steps": result["steps"],
            "error": result["error"]
        }
    
    def get_history(self) -> List[ConversationEntry]:
        """Get conversation history."""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history_summary(self) -> str:
        """Get a formatted summary of conversation history."""
        if not self.conversation_history:
            return "No conversation history yet."
        
        summary = f"Conversation History ({len(self.conversation_history)} interactions)\n"
        summary += "=" * 80 + "\n"
        
        for i, entry in enumerate(self.conversation_history, 1):
            summary += f"\n#{i} [{entry['timestamp']}]\n"
            summary += f"Q: {entry['query']}\n"
            summary += f"Route: {entry['route']} (Reason: {entry['routing_reasoning']})\n"
            summary += f"A: {entry['response'][:200]}{'...' if len(entry['response']) > 200 else ''}\n"
            summary += "-" * 80
        
        return summary


def create_supervisor_graph(api_key: str = None):
    """
    Create the main supervisor routing graph.
    
    Args:
        api_key: Optional API key. If not provided, will try to load from environment.
    """
    # Create stateful graph
    supervisor_graph = SupervisorGraph(api_key)
    return supervisor_graph


def run_query(graph, query: str) -> Dict[str, Any]:
    """
    Helper function to run a query through the graph.
    
    Args:
        graph: SupervisorGraph instance or compiled LangGraph
        query: User query
        
    Returns:
        Dict with response and metadata
    """
    # Handle both SupervisorGraph and compiled graph
    if isinstance(graph, SupervisorGraph):
        return graph.query(query)
    else:
        # Legacy support for compiled graph
        initial_state = {
            "messages": [],
            "query": query,
            "route": "general",  # Default
            "routing_reasoning": "",
            "response": "",
            "steps": [],
            "error": "",
            "conversation_history": []
        }
        
        result = graph.invoke(initial_state)
        
        return {
            "query": query,
            "route": result["route"],
            "routing_reasoning": result["routing_reasoning"],
            "response": result["response"],
            "steps": result["steps"],
            "error": result["error"]
        } 