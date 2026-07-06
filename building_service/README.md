# Building Service

Manages physical building data — addresses, amenity lists, floor counts, geographic coordinates, and RERA property verification status. Buildings are the top-level grouping for rental units.

## Why it's a separate service

Buildings have a different lifecycle than listings. A building gets created once and rarely changes, while listings for its units come and go constantly. Separating them also lets the frontend query building data independently (e.g., for a map view showing building locations) without pulling in all the listing overhead.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for building models with amenity tracking |
| djangorestframework | REST API with viewsets |
| django-filter | Geographic bounding box filters for map views, amenity filters |
| django-cors-headers | CORS for frontend |
| psycopg2-binary | PostgreSQL adapter |
| gunicorn | Production WSGI server |
| PyJWT | JWT verification for protected endpoints |
| drf-spectacular | OpenAPI 3.0 docs |

## Directory Structure

```
building_service/
├── building/
│   ├── models/               # Building, BuildingImage, Amenity models
│   ├── api/
│   │   ├── api_views.py      # BuildingViewSet, AmenityViewSet, public views
│   │   ├── serializers.py    # Building serializers with nested images
│   │   ├── filters.py        # Geographic bounding box + amenity filters
│   │   └── pagination.py     # Custom pagination
│   ├── urls.py               # Router registration
│   ├── admin.py              # Inline admin for building images
│   └── management/commands/  # populate_buildings seed command
├── config/
│   ├── settings.py
│   └── db_router.py
├── Dockerfile
└── requirements.txt
```

## Key Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/api/buildings/buildings/` | List buildings with filtering |
| GET | `/api/buildings/buildings/{id}/` | Building detail (used by application_service) |
| GET | `/api/buildings/buildings/{id}/stats/` | Aggregated stats for a building |
| GET | `/api/buildings/amenities/` | List all amenity types |
| GET | `/api/buildings/public/buildings/` | Public read-only view (no auth) |

The geographic bounding box filter (`min_lat`, `max_lat`, `min_lng`, `max_lng`) is designed for the frontend map view — it returns only buildings within the visible map area.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `JWT_SECRET_KEY` | Yes | JWT verification |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |

## Running Standalone

```bash
docker compose up -d db building_service
```

## API Docs

[http://localhost:8004/api/docs/](http://localhost:8004/api/docs/)
