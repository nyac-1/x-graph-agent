"""Schema definitions for structured outputs."""

FUNCTION_CALL_SCHEMA = {
    "type": "object",
    "properties": {
        "function_name": {
            "type": ["string", "null"],
            "description": "Name of the function to call, or null if no function is needed"
        },
        "parameters": {
            "type": ["object", "null"],
            "description": "Parameters for the function call, or null if no function is needed"
        }
    },
    "required": ["function_name", "parameters"]
}

ROUTING_SCHEMA = {
    "type": "object",
    "properties": {
        "route": {
            "type": "string",
            "enum": ["general", "research"],
            "description": "Which agent to route to based on query complexity"
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation of routing decision"
        }
    },
    "required": ["route", "reasoning"]
}

RESEARCH_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "step": {
                        "type": "integer",
                        "description": "Step number in the plan"
                    },
                    "action": {
                        "type": "string",
                        "description": "What to do in this step"
                    },
                    "tool": {
                        "type": "string",
                        "enum": ["wikipedia", "arxiv", "web_search", "python_repl"],
                        "description": "Which tool to use"
                    },
                    "query": {
                        "type": "string",
                        "description": "Query/code to execute with the tool"
                    }
                },
                "required": ["step", "action", "tool", "query"]
            }
        }
    },
    "required": ["plan"]
} 