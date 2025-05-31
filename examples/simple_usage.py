"""Simple usage example for the multi-agent system."""

import os
from dotenv import load_dotenv
from graph.supervisor_graph import create_supervisor_graph, run_query


def main():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Please set GEMINI_API_KEY in your .env file")
        return
    
    # Create the supervisor graph
    print("Initializing agents...")
    graph = create_supervisor_graph(api_key)
    print("Ready!\n")
    
    # Example 1: Simple calculation (General Q&A)
    query1 = "What is 25 * 47?"
    print(f"Query: {query1}")
    result1 = run_query(graph, query1)
    print(f"Agent: {result1['route']}")
    print(f"Answer: {result1['response']}\n")
    
    # Example 2: Research query
    query2 = "What are the latest developments in quantum computing?"
    print(f"Query: {query2}")
    result2 = run_query(graph, query2)
    print(f"Agent: {result2['route']}")
    print(f"Answer: {result2['response'][:200]}...\n")
    
    # Show steps taken
    if result2['steps']:
        print("Research steps:")
        for step in result2['steps']:
            print(f"- {step['tool']}: {step['input']}")


if __name__ == "__main__":
    main() 