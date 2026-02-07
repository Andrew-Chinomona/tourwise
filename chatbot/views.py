from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db.models import Q
from listings.models import Property
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)


def chatbot_view(request):
    """Render the chatbot interface."""
    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    return render(request, 'chatbot/chatbot.html')


def extract_filters_with_groq(user_query, conversation_history):
    """
    Call Groq API to extract property search filters from natural language.
    
    Args:
        user_query: The user's current message
        conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        dict: Extracted filters or empty dict if no filters found
    """
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        system_prompt = """You are a helpful real estate assistant for properties in Zimbabwe. Your job is to extract search parameters from user queries.

IMPORTANT: Return ONLY a valid JSON object. Do not include any explanatory text before or after the JSON.

Return a JSON object with these fields (all optional):
{
  "property_type": "house|apartment|airbnb|room|guesthouse",
  "bedrooms": number (minimum bedrooms required),
  "bathrooms": number (minimum bathrooms required),
  "city": "string",
  "suburb": "string", 
  "min_price": number,
  "max_price": number,
  "min_area": number,
  "max_area": number
}

Examples:
- "3 bedroom house in Harare under $1000" -> {"property_type": "house", "bedrooms": 3, "city": "Harare", "max_price": 1000}
- "apartment in Borrowdale" -> {"property_type": "apartment", "suburb": "Borrowdale"}
- "show me cheaper ones" (in context) -> {"max_price": <adjusted value based on context>}
- "houses with 2 bathrooms" -> {"property_type": "house", "bathrooms": 2}

If the user asks a general question or makes conversation without search intent, return: {"query_type": "conversation"}
If no filters can be extracted, return: {}"""

        # Build messages for Groq API
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 5 messages for context)
        for msg in conversation_history[-5:]:
            messages.append(msg)
        
        # Add current query
        messages.append({"role": "user", "content": user_query})
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=500
        )
        
        # Extract and parse JSON response
        content = response.choices[0].message.content.strip()
        
        # Try to find JSON in the response
        if content.startswith('{') and content.endswith('}'):
            filters = json.loads(content)
        else:
            # Try to extract JSON from markdown code blocks
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
                filters = json.loads(json_str)
            elif '```' in content:
                json_str = content.split('```')[1].split('```')[0].strip()
                filters = json.loads(json_str)
            else:
                # Try to parse as-is
                filters = json.loads(content)
        
        logger.info(f"Extracted filters: {filters}")
        return filters
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}, content: {content}")
        return {}
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return {}


def query_properties(filters):
    """
    Query the Property database using extracted filters.
    
    Args:
        filters: Dictionary of search parameters
    
    Returns:
        QuerySet of matching properties
    """
    # Base filter: only paid listings
    query = Q(is_paid=True)
    
    # Apply filters
    if filters.get('property_type'):
        query &= Q(property_type=filters['property_type'])
    
    if filters.get('bedrooms'):
        query &= Q(bedrooms__gte=filters['bedrooms'])
    
    if filters.get('bathrooms'):
        query &= Q(bathrooms__gte=filters['bathrooms'])
    
    if filters.get('city'):
        query &= Q(city__iexact=filters['city'])
    
    if filters.get('suburb'):
        query &= Q(suburb__iexact=filters['suburb'])
    
    if filters.get('max_price'):
        query &= Q(price__lte=filters['max_price'])
    
    if filters.get('min_price'):
        query &= Q(price__gte=filters['min_price'])
    
    if filters.get('min_area'):
        query &= Q(area__gte=filters['min_area'])
    
    if filters.get('max_area'):
        query &= Q(area__lte=filters['max_area'])
    
    # Execute query with limit
    properties = Property.objects.filter(query).select_related('currency').prefetch_related('images')[:10]
    
    return properties


def format_response(properties, user_query, filters):
    """
    Generate a friendly conversational response based on search results.
    
    Args:
        properties: QuerySet of matching properties
        user_query: The user's original query
        filters: Extracted filters
    
    Returns:
        str: Conversational response message
    """
    count = properties.count()
    
    if count == 0:
        return "I couldn't find any properties matching your criteria. Try adjusting your search parameters, or I can help you explore other options!"
    
    # Build response based on filters
    criteria_parts = []
    
    if filters.get('bedrooms'):
        criteria_parts.append(f"{filters['bedrooms']}+ bedroom")
    
    if filters.get('property_type'):
        criteria_parts.append(filters['property_type'])
    
    if filters.get('city'):
        criteria_parts.append(f"in {filters['city']}")
    elif filters.get('suburb'):
        criteria_parts.append(f"in {filters['suburb']}")
    
    if filters.get('max_price'):
        criteria_parts.append(f"under ${filters['max_price']}")
    
    criteria_str = " ".join(criteria_parts) if criteria_parts else "your criteria"
    
    if count == 1:
        return f"I found 1 property matching {criteria_str}:"
    else:
        return f"I found {count} properties matching {criteria_str}:"


@require_http_methods(["POST"])
def chatbot_query_view(request):
    """
    Handle chatbot queries: extract filters, search properties, return results.
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or initialize conversation history
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []
        
        conversation_history = request.session['chat_history']
        
        # Extract filters using Groq
        filters = extract_filters_with_groq(user_message, conversation_history)
        
        # Check if this is a conversational query (no search intent)
        if filters.get('query_type') == 'conversation':
            response_message = "I'm here to help you find properties! You can ask me things like 'Show me 3 bedroom houses in Harare under $1500' or 'Find apartments in Borrowdale'."
            properties_data = []
        elif not filters or len(filters) == 0:
            # No filters extracted - provide helpful guidance
            response_message = "I'd be happy to help you find a property! Could you tell me what you're looking for? For example, you can specify the number of bedrooms, property type, location, or budget."
            properties_data = []
        else:
            # Query database with extracted filters
            properties = query_properties(filters)
            
            # Format response message
            response_message = format_response(properties, user_message, filters)
            
            # Serialize properties for JSON response
            properties_data = []
            for prop in properties:
                properties_data.append({
                    'id': prop.id,
                    'title': prop.title,
                    'property_type': prop.get_property_type_display(),
                    'bedrooms': prop.bedrooms,
                    'bathrooms': prop.bathrooms,
                    'price': str(prop.price),
                    'city': prop.city,
                    'suburb': prop.suburb,
                    'main_image': prop.main_image.url if prop.main_image else None,
                    'street_address': prop.street_address,
                })
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response_message})
        
        # Keep only last 10 messages (5 exchanges) to prevent session bloat
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        request.session['chat_history'] = conversation_history
        request.session.modified = True
        
        return JsonResponse({
            'message': response_message,
            'properties': properties_data,
            'filters': filters
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in chatbot_query_view: {e}", exc_info=True)
        return JsonResponse({
            'error': 'An error occurred processing your request. Please try again.'
        }, status=500)
