"""Prompts package for multi-agent system."""

from .supervisor_prompts import SUPERVISOR_ROUTING_PROMPT
from .qa_prompts import GENERAL_QA_PROMPT
from .research_prompts import RESEARCH_PLANNING_PROMPT
from .agent_prompts import REACT_AGENT_PROMPT
from .llm_prompts import JSON_GENERATION_PROMPT, FUNCTION_CALL_PROMPT

__all__ = [
    "SUPERVISOR_ROUTING_PROMPT",
    "GENERAL_QA_PROMPT",
    "RESEARCH_PLANNING_PROMPT",
    "REACT_AGENT_PROMPT",
    "JSON_GENERATION_PROMPT",
    "FUNCTION_CALL_PROMPT"
] 