from django.urls import path
from . import views  # Import views from this app
from .views import signup_view, login_view, logout_view, home_view, host_dashboard, search_results_view, become_host_view, step_search_view, tenant_dashboard, edit_profile, delete_account

urlpatterns = [
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),  #URL route for user signup
    path('login/', login_view, name='login'),  #Login route(page)
    path('logout/', logout_view, name='logout'),  #Logout route
    path('host/dashboard/', host_dashboard, name='host_dashboard'),
    path('tenant/dashboard/', tenant_dashboard, name='tenant_dashboard'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('account/delete/', delete_account, name='delete_account'),
    path('host/delete-profile-photo/', views.delete_profile_photo, name='delete_profile_photo'),
    path('search/', search_results_view, name='search_results'),
    path('step-search/', step_search_view, name='step_search'),
    path('become-host/', become_host_view, name='become_host'),
]