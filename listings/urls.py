from django.urls import path
from .views import add_property_step1, add_property_step2, add_property_step3, add_property_step4, add_property_step5, add_property_step6,  delete_listing, delete_property_image, edit_listing, upload_property_images, start_property_listing, add_property_step7, add_property_step8, add_property_step9, choose_payment,upload_profile_photo,upload_main_image, property_detail, recent_listings_view, featured_listings_view

urlpatterns = [
    path('add-property/step-1/', add_property_step1, name='add_property_step1'),
    path('add-property/step-2/', add_property_step2, name='add_property_step2'),
    path('add-property/step-3/', add_property_step3, name='add_property_step3'),
    path('add-property/step-4/', add_property_step4, name='add_property_step4'),
    path('add-property/step-5/', add_property_step5, name='add_property_step5'),
    path('add-property/step-6/', add_property_step6, name='add_property_step6'),
    path('add-property/step-7/', add_property_step7, name='add_property_step7'),
    path('add-property/step-8/', add_property_step8, name='add_property_step8'),
    path('add-property/step-9/', add_property_step9, name='add_property_step9'),
    path('delete-listing/<int:property_id>/', delete_listing, name='delete_listing'),
    path('delete-image/<int:image_id>/', delete_property_image, name='delete_property_image'),
    path('upload-images/<int:property_id>/', upload_property_images, name='upload_property_images'),
    path('listings/start/', start_property_listing, name='start_property_listing'),
    path('edit/<int:property_id>/', edit_listing, name='edit_listing'),
    path('choose_payment/',choose_payment, name='choose_payment'),
    path('property/<int:property_id>/upload-profile-photo/', upload_profile_photo, name='upload_profile_photo'),
    path('upload_main_image/<int:property_id>/upload-main-image/', upload_main_image, name='upload_main_image'),
    path('<int:pk>/', property_detail, name='property_detail'),
path('recent/', recent_listings_view, name='recent_listings'),
    path('featured/', featured_listings_view, name='featured_listings'),
]