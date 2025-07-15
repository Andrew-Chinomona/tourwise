# import json
# from django.http import JsonResponse
# from django.http import StreamingHttpResponse
# import time
# from django.views.decorators.csrf import csrf_exempt
# from listings.models import Property
# from rapidfuzz import fuzz
# from django.shortcuts import render
# from chatbot.nl_query_engine import run_nl_query
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# from django.views.decorators.http import require_POST
#
# @require_POST
# @csrf_exempt
# def ai_sql_query(request):
#     """
#     Accepts a POST request with 'message' and returns a response from the LlamaIndex SQL query engine.
#     """
#     user_input = request.POST.get("message", "")
#     if not user_input:
#         return JsonResponse({"error": "No message provided"}, status=400)
#
#     try:
#         result = run_nl_query(user_input)
#         return JsonResponse({"result": str(result)}, status=200)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
#
# def chat_view(request):
#     return render(request, "chat/chat.html")

import json
from django.http import JsonResponse
from django.http import StreamingHttpResponse
import time
from django.views.decorators.csrf import csrf_exempt
from listings.models import Property, Amenity
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
    Now also performs fuzzy matching on property descriptions and amenities.
    """
    user_input = request.POST.get("message", "")
    if not user_input:
        return JsonResponse({"error": "No message provided"}, status=400)

    try:
        result = run_nl_query(user_input)
        # Assume result.response is a list of dicts (rows)
        rows = result.response if isinstance(result.response, list) else []
        if not rows:
            return JsonResponse({"result": "No results found."}, status=200)

        # Fuzzy match on description and amenities
        scored = []
        for row in rows:
            # Get property description
            description = row.get("description", "")
            # Get property id (if available)
            property_id = row.get("id")
            # Get amenities as a string (if available)
            amenities_str = ""
            if property_id:
                try:
                    prop = Property.objects.get(id=property_id)
                    amenities = prop.amenities.all()
                    amenities_str = ", ".join([a.name for a in amenities])
                except Property.DoesNotExist:
                    pass
            # Fuzzy match score for description
            desc_score = fuzz.token_set_ratio(user_input, description)
            # Fuzzy match score for amenities
            amenity_score = fuzz.token_set_ratio(user_input, amenities_str)
            # Combine scores (weighted)
            total_score = desc_score * 0.6 + amenity_score * 0.4
            scored.append((total_score, row))
        # Sort by score descending
        scored.sort(reverse=True, key=lambda x: x[0])
        # Optionally, filter out low scores (e.g., below 40)
        filtered = [row for score, row in scored if score > 40]
        if not filtered:
            filtered = [row for score, row in scored][:3]  # fallback: top 3
        return JsonResponse({"result": filtered}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def chat_view(request):
    return render(request, "chat/chat.html")

