from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.listings.api.api_views import (
    ListingViewSet,
    PublicListingListView,
    PublicListingDetailView
)


router = DefaultRouter()
router.register(r'listings-service', ListingViewSet, basename='listing')

app_name = 'listings_api'

urlpatterns = [

    path('', include(router.urls)),


    path('public/listings-service/', PublicListingListView.as_view(), name='public-listing-list'),
    path('public/listings-service/<int:pk>/', PublicListingDetailView.as_view(), name='public-listing-detail'),
    path('api/', include('listings-service.urls', namespace='listings_api')),
    path('api-auth/', include('rest_framework.urls')),
]

"""
Available API endpoints:

ViewSet endpoints (full CRUD):
- GET    /api/listings-service/                    - List all listings-service (paginated, filterable)
- POST   /api/listings-service/                    - Create a new listing
- GET    /api/listings-service/{id}/               - Retrieve a specific listing
- PUT    /api/listings-service/{id}/               - Update a listing
- PATCH  /api/listings-service/{id}/               - Partial update a listing
- DELETE /api/listings-service/{id}/               - Delete a listing

Custom actions:
- GET    /api/listings-service/available/          - Get available listings-service
- GET    /api/listings-service/verified/           - Get verified listings-service
- GET    /api/listings-service/stats/              - Get listing statistics
- POST   /api/listings-service/{id}/verify/        - Mark listing as verified
- POST   /api/listings-service/{id}/unverify/      - Mark listing as unverified

Public endpoints (read-only):
- GET    /api/public/listings-service/             - List verified available listings-service
- GET    /api/public/listings-service/{id}/        - Get a specific verified listing

Query parameters:
- page=1                                    - Page number
- per_page=15                               - Items per page
- ordering=-rent                            - Order by field (prefix with - for descending)
- min_rent=1000                            - Minimum rent filter
- max_rent=5000                            - Maximum rent filter
- available_from=2024-01-01                - Available from date
- is_verified=true                         - Filter by verification status
- search=brooklyn                          - Search across multiple fields
"""

