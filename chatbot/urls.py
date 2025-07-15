from django.urls import path
from .views import chat_view,ai_sql_query


urlpatterns = [
    path('chat/', chat_view, name='chat'),
path("sql/", ai_sql_query, name="ai_sql_query"),
]
