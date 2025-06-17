from django.urls import path
from .views import add_property_step1

urlpatterns = [
    path('add-property/step-1/', add_property_step1, name='add_property_step1'),
]
