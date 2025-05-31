"""Web search tool wrapper."""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    """Input for the web search tool."""
    query: str = Field(description="Search query for web search")


class WebSearchTool(BaseTool):
    """Web search using DuckDuckGo."""
    
    name: str = "web_search"
    description: str = (
        "Search the web for current information, news, and general knowledge. "
        "Use this when you need up-to-date information or facts about current events, "
        "companies, people, or any topic that might have recent developments."
    )
    args_schema: Type[BaseModel] = WebSearchInput
    
    def __init__(self):
        super().__init__()
        self._search = DuckDuckGoSearchRun()
    
    def _run(self, query: str) -> str:
        """Execute web search and return results."""
        try:
            results = self._search.run(query)
            if not results:
                return "No search results found."
            return f"Web search results for '{query}':\n\n{results}"
        except Exception as e:
            return f"Error performing web search: {type(e).__name__}: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async version - just calls sync version."""
        return self._run(query) 