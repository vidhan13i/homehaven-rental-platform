from django.urls import path, include
from rest_framework.routers import DefaultRouter
from building.api.api_views import (
    BuildingViewSet,
    BuildingImageViewSet,
    PublicBuildingListView,
    PublicBuildingDetailView,
)

router = DefaultRouter()
router.register(r"buildings", BuildingViewSet, basename="building")
router.register(r"building-images", BuildingImageViewSet, basename="building-image")

app_name = "building_api"

urlpatterns = [
    # All ViewSet routes (CRUD + custom actions)
    path("", include(router.urls)),
    # Public-facing endpoints (read-only)
    path(
        "buildings/public/",
        PublicBuildingListView.as_view(),
        name="public-building-list",
    ),
    path(
        "buildings/public/<slug:slug>/",
        PublicBuildingDetailView.as_view(),
        name="public-building-detail",
    ),
    # DRF browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),
]


"""
═══════════════════════════════════════════════════════════════════════════════
 COMPLETE API ENDPOINT MAP
 (All routed via Nginx gateway on http://localhost:8000)
═══════════════════════════════════════════════════════════════════════════════

 BUILDINGS (/api/buildings/)
 ─────────────────────────────────────────────────────────────────────────────
  GET    /api/buildings/buildings/               → List all buildings
  POST   /api/buildings/buildings/               → Create a new building
  GET    /api/buildings/buildings/{id}/          → Building detail (with images)
  PUT    /api/buildings/buildings/{id}/          → Full update
  PATCH  /api/buildings/buildings/{id}/          → Partial update
  DELETE /api/buildings/buildings/{id}/          → Delete

  GET    /api/buildings/buildings/stats/         → Aggregate statistics
  GET    /api/buildings/buildings/cities/        → Unique city list
  GET    /api/buildings/buildings/nearby/        → Geo-nearby query
  GET    /api/buildings/buildings/top-rated/     → Top-rated buildings
  GET    /api/buildings/buildings/{id}/images/   → All building images
  POST   /api/buildings/buildings/{id}/add_image/→ Add image to building

  GET    /api/buildings/buildings/public/        → RERA-verified buildings
  GET    /api/buildings/buildings/public/{slug}/ → Public detail (by slug)

 BUILDING IMAGES (standalone CRUD)
 ─────────────────────────────────────────────────────────────────────────────
  GET/POST/PUT/DELETE  /api/buildings/building-images/ → Image CRUD
"""
