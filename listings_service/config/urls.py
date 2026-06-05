from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Views live at listings/api/views.py → import path is listings.api.views
from listings.api.views import ListingViewSet, PublicListingListView, PublicListingDetailView

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listing')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/listings/', include(router.urls)),
    path('api/listings/public/', PublicListingListView.as_view(), name='public-listing-list'),
    path('api/listings/public/<int:pk>/', PublicListingDetailView.as_view(), name='public-listing-detail'),
]