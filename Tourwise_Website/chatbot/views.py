import logging
from rapidfuzz import fuzz
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from listings.models import Property, Amenity

logger = logging.getLogger(__name__)

@login_required
def chat_view(request):
    return render(request, 'chat/chat.html')

import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Optional: use Groq or OpenAI based on environment
ENVIRONMENT = os.getenv("CHAT_ENV", "dev")

if ENVIRONMENT == "dev":
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    MODEL_NAME = "llama3-8b-8192"
else:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = "gpt-4"

@csrf_exempt
def chatbot_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message:
                return JsonResponse({"error": "No message provided"}, status=400)

            # Call the LLM
            if ENVIRONMENT == "dev":
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a helpful property chatbot."},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                )
                reply = response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a helpful property chatbot."},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                )
                reply = response["choices"][0]["message"]["content"]

            return JsonResponse({"reply": reply})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
