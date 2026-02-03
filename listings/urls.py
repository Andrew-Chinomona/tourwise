from django.urls import path
from .views import (
    # Unified form views
    add_property_listing, edit_draft_listing, start_property_listing,
    # Other views
    delete_listing, delete_property_image, edit_listing, upload_property_images,
    choose_payment, upload_profile_photo, upload_main_image, property_detail, 
    recent_listings_view, featured_listings_view, location_suggestions, delete_draft_listing
)
from rest_framework.routers import DefaultRouter
from .api_views import PropertyViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')

urlpatterns = [
    # Unified single-page form
    path('add-property/', add_property_listing, name='add_property_listing'),
    path('edit-draft/<int:property_id>/', edit_draft_listing, name='edit_draft_listing'),
    path('listings/start/', start_property_listing, name='start_property_listing'),  # Redirects to new form
    
    # Property management
    path('delete-listing/<int:property_id>/', delete_listing, name='delete_listing'),
    path('delete-image/<int:image_id>/', delete_property_image, name='delete_property_image'),
    path('upload-images/<int:property_id>/', upload_property_images, name='upload_property_images'),
    path('edit/<int:property_id>/', edit_listing, name='edit_listing'),
    path('drafts/delete/<int:property_id>/', delete_draft_listing, name='delete_draft_listing'),
    
    # Payment
    path('choose_payment/', choose_payment, name='choose_payment'),
    
    # Image uploads
    path('property/<int:property_id>/upload-profile-photo/', upload_profile_photo, name='upload_profile_photo'),
    path('property/<int:property_id>/upload-main-image/', upload_main_image, name='upload_main_image'),
    
    # Public views
    path('<int:pk>/', property_detail, name='property_detail'),
    path('recent/', recent_listings_view, name='recent_listings'),
    path('featured/', featured_listings_view, name='featured_listings'),
    path('api/locations/', location_suggestions, name='location_suggestions'),
]
urlpatterns += router.urls