from django.urls import path
from .views import chat_view, ai_sql_query, get_chat_history, get_session_messages, start_new_chat

urlpatterns = [
    path('chat/', chat_view, name='chat'),
    path("sql/", ai_sql_query, name="ai_sql_query"),
    path("history/", get_chat_history, name="get_chat_history"),
    path("session/<uuid:session_id>/", get_session_messages, name="get_session_messages"),
    path("new-chat/", start_new_chat, name="start_new_chat"),
]
