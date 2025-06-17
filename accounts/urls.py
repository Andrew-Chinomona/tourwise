from django.urls import path
from . import views  # Import views from this app

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),  # URL route for user signup
]














#homepage template
from .views import signup_view
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("Placeholder Home Page")

urlpatterns = [
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),
]
