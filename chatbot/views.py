from django.shortcuts import render


def chatbot_view(request):
    """Render the chatbot interface."""
    return render(request, 'chatbot/chatbot.html')
