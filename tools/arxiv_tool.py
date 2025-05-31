"""ArXiv tool wrapper for research papers."""

from langchain_community.tools import ArxivQueryRun
from langchain_community.utilities import ArxivAPIWrapper
from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class ArxivInput(BaseModel):
    """Input for the ArXiv tool."""
    query: str = Field(description="Search query for ArXiv papers")


class ArxivTool(BaseTool):
    """ArXiv search for research papers and academic content."""
    
    name: str = "arxiv"
    description: str = (
        "Search ArXiv for research papers, academic publications, and scientific literature. "
        "Use this for cutting-edge research, technical papers, preprints, and academic studies "
        "in physics, mathematics, computer science, and other scientific fields."
    )
    args_schema: Type[BaseModel] = ArxivInput
    
    def __init__(self):
        super().__init__()
        # Configure ArXiv wrapper
        arxiv_wrapper = ArxivAPIWrapper(
            top_k_results=5,  # Return top 5 papers
            doc_content_chars_max=4000,  # Limit abstract length
        )
        self._search = ArxivQueryRun(api_wrapper=arxiv_wrapper)
    
    def _run(self, query: str) -> str:
        """Execute ArXiv search and return results."""
        try:
            results = self._search.run(query)
            if not results:
                return f"No ArXiv papers found for '{query}'."
            return f"ArXiv papers for '{query}':\n\n{results}"
        except Exception as e:
            return f"Error searching ArXiv: {type(e).__name__}: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async version - just calls sync version."""
        return self._run(query) 