"""Wikipedia search tool for encyclopedic knowledge."""

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class WikipediaInput(BaseModel):
    """Input for the Wikipedia tool."""
    query: str = Field(description="Search query for Wikipedia")


class WikipediaTool(BaseTool):
    """Wikipedia search for encyclopedic knowledge."""
    
    name: str = "wikipedia"
    description: str = (
        "Search Wikipedia for encyclopedic knowledge, historical information, "
        "scientific concepts, biographies, and well-established facts. "
        "Use this for academic or educational queries that need reliable, structured information."
    )
    args_schema: Type[BaseModel] = WikipediaInput
    
    def __init__(self):
        super().__init__()
        # Configure Wikipedia wrapper with reasonable defaults
        wiki_wrapper = WikipediaAPIWrapper(
            top_k_results=3,  # Return top 3 results
            doc_content_chars_max=4000  # Limit content length
        )
        self._search = WikipediaQueryRun(api_wrapper=wiki_wrapper)
    
    def _run(self, query: str) -> str:
        """Execute Wikipedia search and return results."""
        try:
            results = self._search.run(query)
            if not results:
                return f"No Wikipedia articles found for '{query}'."
            return f"Wikipedia results for '{query}':\n\n{results}"
        except Exception as e:
            return f"Error searching Wikipedia: {type(e).__name__}: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async version - just calls sync version."""
        return self._run(query) 