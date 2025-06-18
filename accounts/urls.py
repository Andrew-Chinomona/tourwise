from django.urls import path
from . import views  # Import views from this app
from .views import signup_view, login_view, logout_view, home_view, host_dashboard

urlpatterns = [
    path('', home_view, name='home'),   #homepage placeholder
    path('signup/', views.signup_view, name='signup'),  # URL route for user signup
    path('login/', login_view, name='login'),  # Login route(page)
    path('logout/', logout_view, name='logout'),  # Logout route
    path('host/dashboard/', host_dashboard, name='host_dashboard'),
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
