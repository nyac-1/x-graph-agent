"""Custom Gemini LLM with exactly 1 method and rate limiting."""

import time
import google.generativeai as genai


class CustomGeminiLLM:
    """Custom Gemini LLM wrapper with exactly 1 method."""
    
    def __init__(self, api_key: str):
        """Initialize the Gemini LLM with API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def text_to_text(self, prompt: str) -> str:
        """
        Basic text completion method.
        
        Args:
            prompt: Input text prompt
            
        Returns:
            Generated text response
        """
        try:
            # Rate limiting - 1 second between calls
            time.sleep(1)
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error in text_to_text: {str(e)}"


if __name__ == "__main__":
    # Test the custom LLM (requires GEMINI_API_KEY environment variable)
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        llm = CustomGeminiLLM(api_key)
        
        # Test text_to_text
        print("Testing text_to_text:")
        result = llm.text_to_text("What is the capital of France?")
        print(f"Result: {result}")
    else:
        print("GEMINI_API_KEY not found") 