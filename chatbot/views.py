import json
from django.http import JsonResponse
from django.http import StreamingHttpResponse
import time
from django.views.decorators.csrf import csrf_exempt
from listings.models import Property
from rapidfuzz import fuzz
from django.shortcuts import render
from chatbot.nl_query_engine import run_nl_query
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
@csrf_exempt
def ai_sql_query(request):
    """
    Accepts a POST request with 'message' and returns a response from the LlamaIndex SQL query engine.
    """
    user_input = request.POST.get("message", "")
    if not user_input:
        return JsonResponse({"error": "No message provided"}, status=400)

    try:
        result = run_nl_query(user_input)
        return JsonResponse({"result": str(result)}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def chat_view(request):
    return render(request, "chat/chat.html")
