from django.urls import path, include
from rest_framework.routers import DefaultRouter
from listings.api.views import (
    # Listing views
    ListingViewSet,
    PublicListingListView,
    PublicListingDetailView,
    # Unit views
    UnitViewSet,
    # Agent views
    AgentViewSet,
    # Image views
    UnitImageViewSet,
    AgentImageViewSet,
)

router = DefaultRouter()
router.register(r"listings", ListingViewSet, basename="listing")
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"agents", AgentViewSet, basename="agent")
router.register(r"unit-images", UnitImageViewSet, basename="unit-image")
router.register(r"agent-images", AgentImageViewSet, basename="agent-image")

app_name = "listings_api"

urlpatterns = [
    path(
        "listings/public/", PublicListingListView.as_view(), name="public-listing-list"
    ),
    path(
        "listings/public/<uuid:pk>/",
        PublicListingDetailView.as_view(),
        name="public-listing-detail",
    ),
    path("", include(router.urls)),
    # DRF browsable API login/logout
    path("api-auth/", include("rest_framework.urls")),
]


"""
═══════════════════════════════════════════════════════════════════════════════
 COMPLETE API ENDPOINT MAP
 (All routed via Nginx gateway on http://localhost:8000)
═══════════════════════════════════════════════════════════════════════════════

 LISTINGS (/api/listings/)
 ─────────────────────────────────────────────────────────────────────────────
  GET    /api/listings/                     → List all listings (paginated)
  POST   /api/listings/                     → Create a new listing
  GET    /api/listings/{id}/               → Get listing detail (with unit data)
  PUT    /api/listings/{id}/               → Full update
  PATCH  /api/listings/{id}/               → Partial update
  DELETE /api/listings/{id}/               → Delete

  GET    /api/listings/available/           → Available listings only
  GET    /api/listings/verified/            → Verified listings only
  GET    /api/listings/stats/               → Aggregate statistics
  POST   /api/listings/{id}/verify/         → Mark as verified
  POST   /api/listings/{id}/unverify/       → Mark as unverified
  GET    /api/listings/public/              → Public verified + available
  GET    /api/listings/public/{id}/         → Public single listing

 UNITS (/api/listings/units/)
 ─────────────────────────────────────────────────────────────────────────────
  GET    /api/listings/units/               → List all units
  POST   /api/listings/units/               → Create a new unit
  GET    /api/listings/units/{id}/          → Unit detail (with images)
  PUT    /api/listings/units/{id}/          → Full update
  PATCH  /api/listings/units/{id}/          → Partial update
  DELETE /api/listings/units/{id}/          → Delete

  GET    /api/listings/units/{id}/listings/ → All listings for this unit
  GET    /api/listings/units/{id}/images/   → All images for this unit
  POST   /api/listings/units/{id}/add_image/→ Add an image to this unit

 AGENTS (/api/listings/agents/)
 ─────────────────────────────────────────────────────────────────────────────
  GET    /api/listings/agents/              → List all agents
  POST   /api/listings/agents/              → Register a new agent
  GET    /api/listings/agents/{id}/         → Agent detail (with images)
  PUT    /api/listings/agents/{id}/         → Full update
  PATCH  /api/listings/agents/{id}/         → Partial update
  DELETE /api/listings/agents/{id}/         → Delete

  GET    /api/listings/agents/{id}/units/    → Units managed by this agent
  GET    /api/listings/agents/{id}/listings/ → Listings by this agent
  POST   /api/listings/agents/{id}/verify/   → Mark agent as verified
  POST   /api/listings/agents/{id}/add_image/→ Add an agent profile image
  GET    /api/listings/agents/verified/      → Verified agents only
  GET    /api/listings/agents/stats/         → Agent statistics

 IMAGES (standalone CRUD)
 ─────────────────────────────────────────────────────────────────────────────
  GET/POST/PUT/DELETE  /api/listings/unit-images/    → Unit image CRUD
  GET/POST/PUT/DELETE  /api/listings/agent-images/   → Agent image CRUD
"""
