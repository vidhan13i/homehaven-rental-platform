from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.api_views import (ListingViewSet, PublicListingListView, PublicListingDetailView)

router = DefaultRouter()
router.register(r'listings-service', ListingViewSet, basename='listing')

urlpatterns = [
    path('', include(router.urls)),
    path('public/listings-service/', PublicListingListView.as_view(), name='public-listing-list'),
    path('public/listings-service/<int:pk>/', PublicListingDetailView.as_view(), name='public-listing-detail'),
]