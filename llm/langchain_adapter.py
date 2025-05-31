"""LangChain adapter for the custom 1-method Gemini LLM."""

import json
from typing import Any, Dict, List, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field
from .custom_gemini import CustomGeminiLLM
from prompts.llm_prompts import JSON_GENERATION_PROMPT, FUNCTION_CALL_PROMPT


class LangChainGeminiAdapter(LLM):
    """LangChain-compatible wrapper for CustomGeminiLLM."""
    
    custom_llm: CustomGeminiLLM = Field(default=None, exclude=True)
    api_key: str = Field(default=None, exclude=True)
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.custom_llm = CustomGeminiLLM(api_key)
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Standard LangChain _call method using our custom LLM."""
        return self.custom_llm.text_to_text(prompt)
    
    @property
    def _llm_type(self) -> str:
        """Return LLM type for LangChain."""
        return "custom_gemini"
    
    @property 
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters."""
        return {"model_name": "custom_gemini_1_method"}
    
    def _clean_json_response(self, response: str) -> str:
        """Clean up JSON response by removing markdown formatting."""
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
    
    # Expose custom methods for direct access when needed
    def get_structured_response(self, prompt: str, schema: dict) -> dict:
        """Get structured JSON response using text_to_text with formatting."""
        try:
            # Format prompt for JSON generation
            formatted_prompt = JSON_GENERATION_PROMPT.format(
                prompt=prompt,
                schema=json.dumps(schema, indent=2)
            )
            
            # Use text_to_text
            response = self.custom_llm.text_to_text(formatted_prompt)
            
            # Clean and parse response
            try:
                cleaned = self._clean_json_response(response)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": response
                }
        except Exception as e:
            return {
                "error": f"Error getting structured response: {str(e)}"
            }
    
    def get_function_call(self, prompt: str, functions: List[dict]) -> dict:
        """Get function call decision using text_to_text with formatting."""
        try:
            # Format prompt for function calling
            formatted_prompt = FUNCTION_CALL_PROMPT.format(
                prompt=prompt,
                functions=json.dumps(functions, indent=2)
            )
            
            # Use text_to_text
            response = self.custom_llm.text_to_text(formatted_prompt)
            
            # Clean and parse response
            try:
                cleaned = self._clean_json_response(response)
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {
                    "function_name": None,
                    "parameters": None,
                    "error": "Failed to parse function call response",
                    "raw_response": response
                }
        except Exception as e:
            return {
                "function_name": None,
                "parameters": None,
                "error": f"Error getting function call: {str(e)}"
            } 