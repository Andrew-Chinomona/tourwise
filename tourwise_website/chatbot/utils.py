import os
import json
from django.conf import settings

def extract_search_params_from_llm(message, client, model_name, mode="dev"):
    """
    Sends the user message to the LLM (Groq or OpenAI) to extract search filters
    """
    prompt = f"""
    You are a smart property assistant.
    Extract the following search parameters from this user message:
    - City
    - Suburb
    - Maximum price
    - Property type
    - Amenities list
    - Special keywords like "pet-friendly", "garden"

    Return them in JSON format.

    User message: "{message}"
    """

    if mode == "dev":
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You extract property filters from natural language."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        text = response.choices[0].message.content
    else:
        import openai
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You extract property filters from natural language."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        text = response["choices"][0]["message"]["content"]

    # Handle JSON wrapping
    try:
        return json.loads(text.strip().strip("```json").strip("```"))
    except json.JSONDecodeError:
        return {}
