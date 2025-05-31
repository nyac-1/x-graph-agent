"""LLM-specific prompts for structured output generation."""

JSON_GENERATION_PROMPT = """{prompt}

You MUST respond with valid JSON that exactly matches this schema:
{schema}

Important rules:
1. Output ONLY valid JSON, no other text before or after
2. Follow the schema structure exactly
3. Use proper JSON syntax (double quotes for strings, no trailing commas)
4. If uncertain about a value, use null rather than making something up
5. Do not wrap the JSON in markdown code blocks

JSON Response:"""

FUNCTION_CALL_PROMPT = """{prompt}

Available functions:
{functions}

You need to decide if a function should be called based on the user's request.

If a function should be called, respond with EXACTLY this JSON format:
{{
    "function_name": "name_of_function",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

If no function is needed, respond with EXACTLY:
{{
    "function_name": null,
    "parameters": null
}}

Important:
- Output ONLY valid JSON, no markdown formatting
- Match function names exactly as provided
- Include all required parameters
- Use null values appropriately
- Do not add any text before or after the JSON

JSON Response:""" 