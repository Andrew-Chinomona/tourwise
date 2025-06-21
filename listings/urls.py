from django.urls import path
from .views import add_property_step1, add_property_step2, add_property_step3, add_property_step4, add_property_step5, add_property_step6, add_property_step7, add_property_step8, choose_payment, edit_listing, delete_listing

urlpatterns = [
    path('add-property/step-1/', add_property_step1, name='add_property_step1'),
    path('add-property/step-2/', add_property_step2, name='add_property_step2'),
    path('add-property/step-3/', add_property_step3, name='add_property_step3'),
    path('add-property/step-4/', add_property_step4, name='add_property_step4'),
    path('add-property/step-5/', add_property_step5, name='add_property_step5'),
    path('add-property/step-6/', add_property_step6, name='add_property_step6'),
    path('add-property/step-7/', add_property_step7, name='add_property_step7'),
    path('add-property/step-8/', add_property_step8, name='add_property_step8'),
    path('add-property/choose-payment/', choose_payment, name='choose_payment'),
path('edit-listing/<int:property_id>/', edit_listing, name='edit_listing'),
    path('delete-listing/<int:property_id>/', delete_listing, name='delete_listing'),
]
