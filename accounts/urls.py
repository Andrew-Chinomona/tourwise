from django.urls import path
from . import views  # Import views from this app

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),  # URL route for user signup
]


#this will be deleted
from .views import signup_view, home_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('', home_view, name='home'),  #  This fixes the missing 'home'
]
from .views import signup_view, home_view, login_view

urlpatterns = [
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),  #  fixes the error
]
