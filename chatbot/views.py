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
    Enriches partial SQL data with full ORM data from Django.
    """
    user_input = request.POST.get("message", "").strip()
    if not user_input:
        return JsonResponse({"error": "No message provided"}, status=400)

    try:
        result = run_nl_query(user_input)

        # Normalize SQL response to list of dicts
        rows = []
        try:
            raw_result = result.response
            if isinstance(raw_result, str):
                parsed = ast.literal_eval(raw_result)
            else:
                parsed = raw_result

            col_keys = result.metadata.get("col_keys", [])
            for tup in parsed:
                row = {}
                if isinstance(tup, tuple):
                    row = dict(zip(col_keys, tup))
                elif isinstance(tup, dict):
                    row = tup

                # ✅ Try to enrich with full data from database
                try:
                    prop = None
                    if "id" in row:
                        prop = Property.objects.get(id=row["id"])
                    elif "title" in row:
                        prop = Property.objects.filter(title__icontains=row["title"]).first()

                    if prop:
                        row["id"] = prop.id
                        row["main_image"] = prop.main_image.url if prop.main_image else ""
                        row["price"] = prop.price
                        row["street_address"] = prop.street_address
                        row["suburb"] = prop.suburb
                        row["city"] = prop.city
                        row["title"] = prop.title
                        row["description"] = prop.description
                except Property.DoesNotExist:
                    pass

                rows.append(row)
        except Exception as parse_err:
            print("❌ Error parsing SQL result:", parse_err)
            return JsonResponse({"error": "Failed to parse database results."}, status=500)

        if not rows:
            return JsonResponse({"result": "No results found."}, status=200)

        # Fuzzy scoring
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

        # Sort by score descending
        scored.sort(reverse=True, key=lambda x: x[0])
        # Return all results, sorted by score
        filtered = [row for score, row in scored]
        return JsonResponse({"result": filtered}, status=200)

    except Exception as e:
        print("🔥 Error in ai_sql_query:", str(e))
        return JsonResponse({"error": str(e)}, status=500)


def chat_view(request):
    """
    Renders the chatbot frontend page.
    """
    return render(request, "chat/chat.html")
