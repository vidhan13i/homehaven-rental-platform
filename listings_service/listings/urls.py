from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.api.views import (
    ListingViewSet,
    PublicListingListView,
    PublicListingDetailView
)

router = DefaultRouter()
router.register(r'', ListingViewSet, basename='listing')

app_name = 'listings_api'

urlpatterns = [
    path('', include(router.urls)),
    path('public/', PublicListingListView.as_view(), name='public-listing-list'),
    path('public/<uuid:pk>/', PublicListingDetailView.as_view(), name='public-listing-detail'),
    path('api-auth/', include('rest_framework.urls')),
]

"""
Available API endpoints (all routed via Nginx gateway from port 8000):

ViewSet endpoints (full CRUD):
- GET    /api/listings/           - List all listings (paginated, filterable)
- POST   /api/listings/           - Create a new listing
- GET    /api/listings/{id}/      - Retrieve a specific listing
- PUT    /api/listings/{id}/      - Update a listing
- PATCH  /api/listings/{id}/      - Partial update a listing
- DELETE /api/listings/{id}/      - Delete a listing

Custom actions:
- GET    /api/listings/available/ - Get available listings
- GET    /api/listings/verified/  - Get verified listings
- GET    /api/listings/stats/     - Get listing statistics
- POST   /api/listings/{id}/verify/   - Mark listing as verified
- POST   /api/listings/{id}/unverify/ - Mark listing as unverified

Public endpoints (read-only, no auth required):
- GET    /api/listings/public/         - List verified available listings
- GET    /api/listings/public/{id}/    - Get a specific verified listing
"""
