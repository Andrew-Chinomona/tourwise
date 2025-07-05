from django.urls import path
from . import views
from listings import views as listing_views

urlpatterns = [
    path('initiate/<int:property_id>/', views.initiate_payment, name='initiate_payment'),
    path('complete/', views.payment_complete, name='payment_complete'),
    path('update/', views.payment_update, name='payment_update'),
    path('status/<str:reference>/', views.payment_status, name='payment_status'),
    path('simulate/<str:reference>/', views.simulate_payment_success, name='simulate_payment_success'),
    path('choose/', listing_views.choose_payment, name='choose_payment')
]
