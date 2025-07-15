import os
from groq import Groq
import json

# Setup Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL_NAME = "llama3-8b-8192"

def extract_query_components(user_input):
    """
    Sends user input to LLaMA via Groq to extract structured search filters.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a real estate assistant. Extract search filters from the user's message. Return JSON with: city, suburb, max_price, property_type, amenities, keywords."
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.3,
        max_tokens=256
    )

    content = response.choices[0].message.content.strip()

    try:
        # If wrapped in code block, remove it
        content = content.strip("```json").strip("```")
        return json.loads(content)
    except Exception as e:
        print("Error parsing Groq output:", e)
        return {}
