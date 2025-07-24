import json
import ast
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from listings.models import Property, Amenity
from rapidfuzz import fuzz
from chatbot.nl_query_engine import run_nl_query
from .models import ChatSession, ChatMessage
import uuid
from decimal import Decimal


def convert_decimal_to_float(obj):
    """Recursively convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    else:
        return obj


def get_or_create_session(request):
    """Get or create a chat session for the current user"""
    session_id = request.session.get('chat_session_id')

    if session_id:
        try:
            session = ChatSession.objects.get(session_id=session_id, is_active=True)
            return session
        except ChatSession.DoesNotExist:
            pass

    # Create new session
    session = ChatSession.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_id=str(uuid.uuid4()),
        is_active=True
    )
    request.session['chat_session_id'] = session.session_id
    return session


def save_message(session, sender, content, message_type='text', metadata=None):
    """Save a message to the database"""
    # Convert any Decimal values in metadata before saving
    if metadata:
        try:
            # Deep conversion of all Decimal values
            metadata = convert_decimal_to_float(metadata)
            # Test JSON serialization to ensure it's valid
            json.dumps(metadata)
        except (TypeError, ValueError) as e:
            print(f"🔥 Error converting metadata: {e}")
            # Fallback: convert everything to basic types
            metadata = _force_convert_to_basic_types(metadata)
            print(f"🔥 Converted metadata: {metadata}")

    # Final safety check - ensure metadata is JSON safe
    if metadata:
        try:
            json.dumps(metadata)
        except Exception as e:
            print(f"🔥 Final metadata conversion failed: {e}")
            metadata = _force_convert_to_basic_types(metadata)

    return ChatMessage.objects.create(
        session=session,
        sender=sender,
        content=content,
        message_type=message_type,
        metadata=metadata or {}
    )


def _deep_convert_to_json_safe(obj):
    """Convert any object to JSON-safe types"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: _deep_convert_to_json_safe(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_deep_convert_to_json_safe(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        return obj


def _force_convert_to_basic_types(obj):
    """Force convert any object to basic JSON-safe types"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {str(key): _force_convert_to_basic_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_force_convert_to_basic_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return [_force_convert_to_basic_types(item) for item in obj]
    else:
        # Convert any other object to string
        try:
            return str(obj)
        except:
            return "Unknown object"


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

    # Get or create chat session
    session = get_or_create_session(request)

    # Save user message
    user_message = save_message(session, 'user', user_input)

    # Generate title for session if it's the first user message
    if session.messages.filter(sender='user').count() == 1:
        session.generate_title()

    try:
        result = run_nl_query(user_input)

        # Convert any Decimal values in the result metadata
        if hasattr(result, 'metadata') and result.metadata:
            result.metadata = convert_decimal_to_float(result.metadata)

        # Convert any Decimal values in the response
        if hasattr(result, 'response') and result.response:
            result.response = convert_decimal_to_float(result.response)

        # Handle conversational responses
        if isinstance(result, dict) and result.get("is_conversational"):
            bot_response = result.get("chat_response", "Hello!")
            # Save bot message
            save_message(session, 'bot', bot_response, 'conversational')
            return JsonResponse({
                "result": result.get("results", []),
                "friendly_message": bot_response
            }, status=200)

        # Normalize SQL response to list of dicts
        rows = []
        try:
            raw_result = result.response
            if isinstance(raw_result, str):
                parsed = ast.literal_eval(raw_result)
            else:
                parsed = raw_result

            # Convert any Decimal values in the raw result
            parsed = convert_decimal_to_float(parsed)

            col_keys = result.metadata.get("col_keys", [])
            for tup in parsed:
                row = {}
                if isinstance(tup, tuple):
                    row = dict(zip(col_keys, tup))
                elif isinstance(tup, dict):
                    row = tup

                # Convert any Decimal values in the row
                row = convert_decimal_to_float(row)

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
                        row["price"] = float(prop.price) if prop.price else None
                        row["street_address"] = prop.street_address
                        row["suburb"] = prop.suburb
                        row["city"] = prop.city
                        row["title"] = prop.title
                        row["description"] = prop.description

                        from listings.models import PropertyImage
                        images = PropertyImage.objects.filter(property=prop).values_list("image", flat=True)
                        row["property_images"] = [img.url for img in images]
                except Property.DoesNotExist:
                    pass

                rows.append(row)
        except Exception as parse_err:
            print("❌ Error parsing SQL result:", parse_err)
            return JsonResponse({"error": "Failed to parse database results."}, status=500)

        if not rows:
            bot_response = "Sorry, I couldn't find any properties matching your request."
            save_message(session, 'bot', bot_response, 'no_results')
            return JsonResponse({"result": "No results found.", "friendly_message": bot_response}, status=200)

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

        # Get friendly message from the result metadata
        friendly_message = result.metadata.get("chat_response", "Here is what I found.")

        # Convert Decimal values to float for JSON serialization
        filtered = _deep_convert_to_json_safe(filtered)

        # Prepare metadata for saving - ensure it's JSON safe
        metadata_for_save = {
            'property_count': len(filtered),
            'properties': filtered  # Use the cleaned filtered data directly
        }

        # Debug: Print the metadata to see what's causing the issue
        print(f"🔥 Metadata before save: {metadata_for_save}")
        print(f"🔥 Metadata type: {type(metadata_for_save)}")

        # Test JSON serialization of metadata
        try:
            json.dumps(metadata_for_save)
            print("✅ Metadata is JSON serializable")
        except Exception as e:
            print(f"🔥 Metadata JSON test failed: {e}")
            # Force convert everything to basic types
            metadata_for_save = _force_convert_to_basic_types(metadata_for_save)
            print(f"🔥 After force conversion: {metadata_for_save}")

            # Test again after conversion
            try:
                json.dumps(metadata_for_save)
                print("✅ Metadata is now JSON serializable after conversion")
            except Exception as e2:
                print(f"🔥 Still failing after conversion: {e2}")
                # Last resort: create a minimal safe metadata
                metadata_for_save = {
                    'property_count': len(filtered),
                    'properties': []
                }

        # Save bot message with property results
        save_message(
            session,
            'bot',
            friendly_message,
            'property_results',
            metadata_for_save
        )

        # Final conversion to ensure all data is JSON serializable
        try:
            response_data = {"result": filtered, "friendly_message": friendly_message}
            # Test JSON serialization
            json.dumps(response_data)
            return JsonResponse(response_data, status=200)
        except (TypeError, ValueError) as json_error:
            print(f"🔥 JSON serialization error: {json_error}")
            print(f"🔥 Problematic data: {filtered}")
            # Fallback: convert everything to strings
            filtered_safe = []
            for item in filtered:
                safe_item = {}
                for key, value in item.items():
                    if isinstance(value, Decimal):
                        safe_item[key] = float(value)
                    elif hasattr(value, '__dict__'):  # Handle any object types
                        safe_item[key] = str(value)
                    else:
                        safe_item[key] = value
                filtered_safe.append(safe_item)

            return JsonResponse({"result": filtered_safe, "friendly_message": friendly_message}, status=200)

    except Exception as e:
        print("🔥 Error in ai_sql_query:", str(e))
        import traceback
        print("🔥 Full traceback:")
        traceback.print_exc()

        # Try to save error message
        try:
            error_message = f"Something went wrong: {str(e)}"
            save_message(session, 'bot', error_message, 'error')
        except Exception as save_error:
            print(f"🔥 Error saving error message: {save_error}")

        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_chat_history(request):
    """Get chat history for the current user"""
    if not request.user.is_authenticated:
        return JsonResponse({"sessions": []})

    sessions = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).prefetch_related('messages')[:20]  # Limit to last 20 sessions

    session_data = []
    for session in sessions:
        session_data.append({
            'id': str(session.id),
            'title': session.title or f"Chat {session.created_at.strftime('%Y-%m-%d %H:%M')}",
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': session.get_message_count(),
            'is_current': session.session_id == request.session.get('chat_session_id')
        })

    return JsonResponse({"sessions": session_data})


@require_GET
def get_session_messages(request, session_id):
    """Get all messages for a specific session"""
    try:
        session = ChatSession.objects.get(id=session_id)

        # Check if user has access to this session
        if request.user.is_authenticated and session.user != request.user:
            return JsonResponse({"error": "Access denied"}, status=403)

        messages = session.messages.all()
        message_data = []

        for message in messages:
            message_data.append({
                'id': str(message.id),
                'sender': message.sender,
                'content': message.content,
                'message_type': message.message_type,
                'metadata': message.metadata,
                'created_at': message.created_at.isoformat()
            })

        return JsonResponse({
            "session": {
                'id': str(session.id),
                'title': session.title,
                'created_at': session.created_at.isoformat()
            },
            "messages": message_data
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)


@require_POST
@csrf_exempt
def start_new_chat(request):
    """Start a new chat session"""
    # Deactivate current session
    current_session_id = request.session.get('chat_session_id')
    if current_session_id:
        try:
            current_session = ChatSession.objects.get(session_id=current_session_id)
            current_session.is_active = False
            current_session.save()
        except ChatSession.DoesNotExist:
            pass

    # Clear session from request
    if 'chat_session_id' in request.session:
        del request.session['chat_session_id']

    return JsonResponse({"success": True})


def chat_view(request):
    """
    Renders the chatbot frontend page.
    """
    return render(request, "chat/chat.html")
