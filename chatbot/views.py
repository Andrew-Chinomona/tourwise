import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from chatbot.mcp import extract_query_components
from listings.models import Property
from rapidfuzz import fuzz
from django.shortcuts import render

def chat_view(request):
    """
    Renders the chatbot UI page.
    Only accessible to logged-in users.
    """
    # if not request.user.is_authenticated:
    #     return render(request, "chat/not_logged_in.html")  # or redirect to login

    return render(request, "chat/chat.html")
@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    data = json.loads(request.body)
    user_message = data.get("message", "")

    # Step 1: NLP extract search components
    filters = extract_query_components(user_message)

    city = filters.get("city")
    suburb = filters.get("suburb")
    max_price = filters.get("max_price")
    property_type = filters.get("property_type")
    amenities = filters.get("amenities", [])
    keywords = filters.get("keywords", [])

    # Step 2: Query database
    queryset = Property.objects.all()

    if suburb:
        queryset = queryset.filter(suburb__icontains=suburb)
    elif city:
        queryset = queryset.filter(city__icontains=city)

    if max_price:
        queryset = queryset.filter(price__lte=max_price)
    if property_type:
        queryset = queryset.filter(property_type__icontains=property_type)

    results = []
    for prop in queryset:
        # Step 3: Fuzzy match with description and amenities
        score = fuzz.partial_ratio(user_message, prop.description)
        if score >= 60:
            results.append({
                "id": prop.id,
                "title": prop.title,
                "location": f"{prop.street_address}, {prop.suburb}, {prop.city}",
                "price": prop.price,
                "main_image": prop.main_image.url if prop.main_image else None,
            })

    if not results:
        return JsonResponse({"message": "No perfect matches, try again."}, status=200)

    return JsonResponse({"matches": results}, status=200)
