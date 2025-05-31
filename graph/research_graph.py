"""Research planning and execution graph."""

from typing import List, Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from llm.langchain_adapter import LangChainGeminiAdapter
from agents.research_agent import ResearchAgent


class ResearchState(TypedDict):
    """State for the research planning graph."""
    query: str
    plan: List[Dict[str, Any]]
    executed_steps: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    iteration: int
    max_iterations: int
    final_answer: str
    should_continue: bool


def create_research_graph(llm: LangChainGeminiAdapter):
    """
    Create the research agent planning graph.
    
    Args:
        llm: LangChain-compatible LLM adapter
    """
    research_agent = ResearchAgent(llm)
    
    def planner_node(state: ResearchState) -> ResearchState:
        """Create research plan."""
        query = state["query"]
        
        # Create plan
        plan = research_agent.create_research_plan(query)
        
        return {
            **state,
            "plan": plan,
            "iteration": 0,
            "max_iterations": research_agent.max_iterations,
            "should_continue": len(plan) > 0
        }
    
    def executor_node(state: ResearchState) -> ResearchState:
        """Execute next step in plan."""
        plan = state["plan"]
        executed_steps = state.get("executed_steps", [])
        findings = state.get("findings", [])
        iteration = state.get("iteration", 0)
        
        # Get next step
        next_step_idx = len(executed_steps)
        if next_step_idx >= len(plan):
            return {
                **state,
                "should_continue": False
            }
        
        next_step = plan[next_step_idx]
        
        # Execute step
        result = research_agent.execute_step(next_step)
        
        # Update state
        executed_steps.append(next_step)
        findings.append(result)
        iteration += 1
        
        # Determine if we should continue
        should_continue = research_agent.should_continue_research(
            state["query"],
            executed_steps,
            findings,
            plan[next_step_idx + 1:],
            iteration
        )
        
        return {
            **state,
            "executed_steps": executed_steps,
            "findings": findings,
            "iteration": iteration,
            "should_continue": should_continue and iteration < state["max_iterations"]
        }
    
    def synthesizer_node(state: ResearchState) -> ResearchState:
        """Synthesize findings into final answer."""
        query = state["query"]
        findings = state.get("findings", [])
        
        # Synthesize
        final_answer = research_agent.synthesize_findings(query, findings)
        
        return {
            **state,
            "final_answer": final_answer,
            "should_continue": False
        }
    
    def should_continue_decision(state: ResearchState) -> str:
        """Decide whether to continue executing or synthesize."""
        if state.get("should_continue", False):
            return "executor"
        return "synthesizer"
    
    # Build graph
    workflow = StateGraph(ResearchState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # Add edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_conditional_edges(
        "executor",
        should_continue_decision,
        {
            "executor": "executor",  # Loop back for more execution
            "synthesizer": "synthesizer"
        }
    )
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()


def run_research(graph, query: str) -> Dict[str, Any]:
    """
    Helper function to run research through the planning graph.
    
    Args:
        graph: Compiled research graph
        query: Research query
        
    Returns:
        Dict with research results
    """
    initial_state = {
        "query": query,
        "plan": [],
        "executed_steps": [],
        "findings": [],
        "iteration": 0,
        "max_iterations": 5,
        "final_answer": "",
        "should_continue": True
    }
    
    result = graph.invoke(initial_state)
    
    return {
        "query": query,
        "answer": result["final_answer"],
        "plan": result["plan"],
        "findings": result["findings"],
        "completed_steps": len(result["executed_steps"]),
        "total_steps": len(result["plan"])
    } 