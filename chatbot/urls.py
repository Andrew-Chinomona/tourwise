from django.urls import path
from .views import chat_view, chatbot_api

urlpatterns = [
    path('chat/', chat_view, name='chat'),
    path('api/chatbot/', chatbot_api, name='chatbot_api'),
]
