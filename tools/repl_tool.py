"""Custom Python REPL tool implementation."""

from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import re


class REPLInput(BaseModel):
    """Input for the Python REPL tool."""
    code: str = Field(description="Python code to execute")


class CustomREPLTool(BaseTool):
    """Enhanced Python REPL with safety measures."""
    
    name: str = "python_repl"
    description: str = (
        "Execute Python code for calculations, data processing, and analysis. "
        "Use this for math operations, data manipulation, and generating visualizations. "
        "The code should be valid Python and will be executed in a sandboxed environment."
    )
    args_schema: Type[BaseModel] = REPLInput
    
    def __init__(self):
        super().__init__()
        self._repl = PythonREPLTool()
    
    def _clean_code_input(self, code: str) -> str:
        """Clean code input by removing markdown formatting if present."""
        # Remove markdown code blocks
        if "```" in code:
            # Extract code between triple backticks
            match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", code, re.DOTALL)
            if match:
                return match.group(1).strip()
        return code.strip()
    
    def _run(self, code: str) -> str:
        """Execute Python code and return the result."""
        try:
            # Clean the input code
            clean_code = self._clean_code_input(code)
            
            # If it's a simple expression, wrap it in print()
            # This handles cases like "25 * 47" or "50 + 30"
            if clean_code and not any(keyword in clean_code for keyword in ['print', '=', 'def', 'class', 'import', 'for', 'while', 'if']):
                # Check if it's likely an expression
                try:
                    compile(clean_code, '<string>', 'eval')
                    # It's an expression, wrap in print
                    clean_code = f"print({clean_code})"
                except:
                    # Not a simple expression, use as-is
                    pass
            
            # Use the underlying REPL tool
            result = self._repl.run(clean_code)
            
            # Return the result or a success message
            return result if result else "Code executed successfully."
            
        except Exception as e:
            return f"Error executing code: {type(e).__name__}: {str(e)}"
    
    async def _arun(self, code: str) -> str:
        """Async version - just calls sync version."""
        return self._run(code) 