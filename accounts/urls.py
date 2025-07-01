from django.urls import path
from . import views  # Import views from this app
from .views import signup_view, login_view, logout_view, home_view, host_dashboard, search_results_view

urlpatterns = [
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),  #URL route for user signup
    path('login/', login_view, name='login'),  #Login route(page)
    path('logout/', logout_view, name='logout'),  #Logout route
    path('host/dashboard/', host_dashboard, name='host_dashboard'),
    path('search/', search_results_view, name='search_results'),
]