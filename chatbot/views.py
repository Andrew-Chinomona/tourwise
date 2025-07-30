import json
import ast
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.db.models import Q
from listings.models import Property, Amenity
from rapidfuzz import fuzz
from chatbot.nl_query_engine import run_nl_query
from .models import ChatSession, ChatMessage
import uuid
from decimal import Decimal
import time


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

    # Enforce session limit before creating new session
    if request.user.is_authenticated:
        ChatSession.enforce_session_limit(request.user)

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
        return {key: _force_convert_to_basic_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_force_convert_to_basic_types(item) for item in obj]
    else:
        return str(obj)


@require_POST
@csrf_exempt
def ai_sql_query(request):
    """Handle AI chat queries with automatic session management"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)

        # Get or create session
        session = get_or_create_session(request)

        # Save user message
        user_msg = save_message(session, 'user', user_message, 'text')

        # Process with AI
        try:
            from .mcp_core import MCPOrchestrator
            orchestrator = MCPOrchestrator()
            response = orchestrator.process_message(user_message, request)

            # Save AI response
            ai_content = response.get('friendly_message',
                                      'I apologize, but I encountered an error processing your request.')
            ai_msg = save_message(session, 'bot', ai_content, 'text', response)

            # Return response with session info
            return JsonResponse({
                "response": response,
                "session_id": str(session.id),
                "message_id": str(ai_msg.id),
                "timestamp": ai_msg.created_at.isoformat()
            })

        except Exception as ai_error:
            # Save error message
            error_msg = save_message(session, 'bot', f"Something went wrong: {str(ai_error)}", 'error')
            return JsonResponse({
                "error": str(ai_error),
                "session_id": str(session.id),
                "message_id": str(error_msg.id)
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        # Try to save error message
        try:
            session = get_or_create_session(request)
            error_msg = save_message(session, 'bot', f"Something went wrong: {str(e)}", 'error')
        except Exception as save_error:
            print(f"🔥 Error saving error message: {save_error}")

        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_chat_history(request):
    """Get chat history for the current user with real-time updates support"""
    if not request.user.is_authenticated:
        return JsonResponse({"sessions": []})

    # Clean up expired sessions first
    ChatSession.cleanup_expired_sessions()

    # Enforce session limits
    ChatSession.enforce_session_limit(request.user)

    sessions = ChatSession.objects.filter(
        user=request.user,
        is_active=True
    ).prefetch_related('messages')[:10]  # Limit to 10 most recent sessions

    session_data = []
    for session in sessions:
        last_message = session.get_last_message()
        session_data.append({
            'id': str(session.id),
            'session_id': session.session_id,
            'title': session.title or f"Chat {session.created_at.strftime('%Y-%m-%d %H:%M')}",
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': session.get_message_count(),
            'has_ai_response': session.has_ai_response,
            'is_current': session.session_id == request.session.get('chat_session_id'),
            'last_message': {
                'content': last_message.content[:100] + '...' if last_message and len(
                    last_message.content) > 100 else last_message.content if last_message else '',
                'sender': last_message.sender if last_message else None,
                'timestamp': last_message.created_at.isoformat() if last_message else None
            } if last_message else None
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
                'session_id': session.session_id,
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'has_ai_response': session.has_ai_response
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


@require_GET
def chat_history_stream(request):
    """Server-Sent Events endpoint for real-time chat history updates"""

    def event_stream():
        """Generate SSE events for chat history updates"""
        last_check = timezone.now()

        while True:
            try:
                # Check for new messages or session updates
                if request.user.is_authenticated:
                    new_messages = ChatMessage.objects.filter(
                        session__user=request.user,
                        session__is_active=True,
                        created_at__gt=last_check
                    ).select_related('session').order_by('created_at')

                    if new_messages.exists():
                        # Send updated history
                        sessions = ChatSession.objects.filter(
                            user=request.user,
                            is_active=True
                        ).prefetch_related('messages')[:10]

                        session_data = []
                        for session in sessions:
                            last_message = session.get_last_message()
                            session_data.append({
                                'id': str(session.id),
                                'session_id': session.session_id,
                                'title': session.title or f"Chat {session.created_at.strftime('%Y-%m-%d %H:%M')}",
                                'updated_at': session.updated_at.isoformat(),
                                'message_count': session.get_message_count(),
                                'has_ai_response': session.has_ai_response,
                                'is_current': session.session_id == request.session.get('chat_session_id'),
                                'last_message': {
                                    'content': last_message.content[:100] + '...' if last_message and len(
                                        last_message.content) > 100 else last_message.content if last_message else '',
                                    'sender': last_message.sender if last_message else None,
                                    'timestamp': last_message.created_at.isoformat() if last_message else None
                                } if last_message else None
                            })

                        yield f"data: {json.dumps({'type': 'history_update', 'sessions': session_data})}\n\n"

                last_check = timezone.now()
                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                print(f"Error in chat history stream: {e}")
                time.sleep(5)  # Wait longer on error

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@require_POST
@csrf_exempt
def delete_session(request, session_id):
    """Delete a specific chat session"""
    try:
        session = ChatSession.objects.get(id=session_id)

        # Check if user has access to this session
        if request.user.is_authenticated and session.user != request.user:
            return JsonResponse({"error": "Access denied"}, status=403)

        session.delete()
        return JsonResponse({"success": True})

    except ChatSession.DoesNotExist:
        return JsonResponse({"error": "Session not found"}, status=404)


@require_POST
@csrf_exempt
def cleanup_expired_sessions(request):
    """Manually trigger cleanup of expired sessions"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    try:
        expired_count = ChatSession.cleanup_expired_sessions()
        return JsonResponse({
            "success": True,
            "deleted_sessions": expired_count
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def chat_view(request):
    """
    Renders the chatbot frontend page.
    """
    return render(request, "chat/chat.html")
