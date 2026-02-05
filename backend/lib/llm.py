import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Check API Key on load
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("CRITICAL: OPENAI_API_KEY is missing from environment!")
else:
    print(f"LLM Initialized. Key present (starts with {api_key[:8]}...)")

client = OpenAI(api_key=api_key)

def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4o", json_mode: bool = False):
    """
    Calls OpenAI ChatCompletion.
    Supports json_mode to force valid JSON output.
    """
    if not api_key:
        return "Error: OPENAI_API_KEY not configured."

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return f"Error generating response: {str(e)}"
