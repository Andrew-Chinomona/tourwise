from django.urls import path
from .views import (
    chat_view, ai_sql_query, get_chat_history, get_session_messages,
    start_new_chat, chat_history_stream, delete_session, cleanup_expired_sessions
)

urlpatterns = [
    path('chat/', chat_view, name='chat'),
    path("sql/", ai_sql_query, name="ai_sql_query"),
    path("history/", get_chat_history, name="get_chat_history"),
    path("history/stream/", chat_history_stream, name="chat_history_stream"),
    path("session/<uuid:session_id>/", get_session_messages, name="get_session_messages"),
    path("session/<uuid:session_id>/delete/", delete_session, name="delete_session"),
    path("new-chat/", start_new_chat, name="start_new_chat"),
    path("cleanup/", cleanup_expired_sessions, name="cleanup_expired_sessions"),
]
