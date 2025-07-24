from django.urls import path
from .views import chat_view, chatbot_search, chatbot_api

urlpatterns = [
    path('', chat_view, name='chat'),
    path('search/', chatbot_search, name='chatbot_search'),
    path('api/', chatbot_api, name='chatbot_api'),
]