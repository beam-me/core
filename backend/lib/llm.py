import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize client globally or per call. Global is fine for serverless if not reused across requests weirdly.
# Vercel might reuse the container.
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-4o"):
    """
    Calls OpenAI ChatCompletion.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        # Return a safe fallback or re-raise
        return f"Error generating response: {str(e)}"
