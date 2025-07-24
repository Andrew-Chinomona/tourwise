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
    Accepts a POST request with 'message' and returns a response using the MCP architecture.
    Maintains backward compatibility with existing frontend.
    """
    user_input = request.POST.get("message", "").strip()
    if not user_input:
        return JsonResponse({"error": "No message provided"}, status=400)

    try:
        # Import MCP components
        from .mcp_core import MCPContext, get_mcp_orchestrator
        from .response_formatter import MCPResponseFormatter

        # Create MCP context
        context = MCPContext(request)
        context.get_or_create_session()

        # Generate title for session if it's the first user message
        if context.session.messages.filter(sender='user').count() == 0:
            context.session.generate_title()

        # Process message through MCP orchestrator
        orchestrator = get_mcp_orchestrator()
        mcp_response = orchestrator.process_message(user_input, context)

        # Format response for frontend
        response_data = MCPResponseFormatter.format_for_frontend(mcp_response)

        return JsonResponse(response_data, status=200)

    except Exception as e:
        print("🔥 Error in ai_sql_query:", str(e))
        import traceback
        print("🔥 Full traceback:")
        traceback.print_exc()

        # Try to save error message
        try:
            from .mcp_core import MCPContext
            context = MCPContext(request)
            context.get_or_create_session()
            context.save_message('bot', f"Something went wrong: {str(e)}", 'error')
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