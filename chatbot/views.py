import json
import ast
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from listings.models import Property, Amenity
from rapidfuzz import fuzz
from chatbot.nl_query_engine import run_nl_query


@require_POST
@csrf_exempt
def ai_sql_query(request):
    """
    Accepts a POST request with 'message' and returns a response from the LlamaIndex SQL query engine.
    Also performs fuzzy matching on property descriptions and amenities.
    """
    user_input = request.POST.get("message", "").strip()
    if not user_input:
        return JsonResponse({"error": "No message provided"}, status=400)

    try:
        # Run the natural language SQL query
        result = run_nl_query(user_input)

        # Normalize the SQL response to list of dicts
        rows = []
        try:
            raw_result = result.response
            if isinstance(raw_result, str):
                parsed = ast.literal_eval(raw_result)
            else:
                parsed = raw_result

            col_keys = result.metadata.get("col_keys", [])
            for tup in parsed:
                if isinstance(tup, tuple):
                    row = dict(zip(col_keys, tup))
                    rows.append(row)
                elif isinstance(tup, dict):
                    rows.append(tup)
        except Exception as parse_err:
            print("❌ Error parsing SQL result:", parse_err)
            return JsonResponse({"error": "Failed to parse database results."}, status=500)

        # If no results found, return message
        if not rows:
            return JsonResponse({"result": "No results found."}, status=200)

        # Fuzzy match scoring based on description and amenities
        scored = []
        for row in rows:
            description = row.get("description", "")
            property_id = row.get("id")
            amenities_str = ""

            if property_id:
                try:
                    prop = Property.objects.get(id=property_id)
                    amenities = prop.amenities.all()
                    amenities_str = ", ".join([a.name for a in amenities])
                except Property.DoesNotExist:
                    pass

            desc_score = fuzz.token_set_ratio(user_input, description)
            amenity_score = fuzz.token_set_ratio(user_input, amenities_str)
            total_score = desc_score * 0.6 + amenity_score * 0.4
            scored.append((total_score, row))

        scored.sort(reverse=True, key=lambda x: x[0])
        filtered = [row for score, row in scored if score > 40]
        if not filtered:
            filtered = [row for score, row in scored][:3]

        return JsonResponse({"result": filtered}, status=200)

    except Exception as e:
        print("🔥 Error in ai_sql_query:", str(e))
        return JsonResponse({"error": str(e)}, status=500)


def chat_view(request):
    """
    Renders the chatbot frontend page.
    """
    return render(request, "chat/chat.html")
