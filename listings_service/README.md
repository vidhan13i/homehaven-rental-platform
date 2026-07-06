# Listings Service

The core property domain — manages rental listings, units, agents, and property images. This is the most query-heavy service in the platform since browsing listings is what most users spend their time doing.

## Why it's a separate service

Listings have fundamentally different read/write patterns compared to other services. They're read-heavy (hundreds of listing views per write), benefit from aggressive caching, and need complex filtering (price range, location, furnishing, BHK type). Isolating this lets us optimize its database and add caching without affecting other services.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for the relational model (Listing → Unit → Agent), admin panel |
| djangorestframework | REST API with viewsets, pagination, and serializers |
| django-filter | Powers the search/filter UI — price range, furnishing, agent, building |
| django-cors-headers | CORS for the React frontend |
| psycopg2-binary | PostgreSQL adapter |
| gunicorn | Production WSGI server |
| PyJWT | Decodes incoming JWTs for auth |
| confluent-kafka | Publishes `ListingCreated` events |
| drf-spectacular | Auto-generates OpenAPI 3.0 docs |

## Directory Structure

```
listings_service/
├── listings/
│   ├── models/               # Listing, Unit, Agent, UnitImage models
│   ├── api/
│   │   ├── views.py          # ViewSets for all models + image upload
│   │   ├── serializers.py    # Nested serializers (Unit includes Agent, Images)
│   │   └── filters.py        # FilterSets for listings, units, agents
│   ├── urls.py               # Router + public read-only endpoints
│   ├── admin.py              # Inline admin (images inside unit)
│   └── management/commands/  # populate_listings seed data command
├── config/
│   ├── settings.py
│   └── db_router.py
├── Dockerfile
└── requirements.txt
```

## Key Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/api/listings/listings/` | List all listings with filtering |
| POST | `/api/listings/listings/` | Create a new listing |
| GET | `/api/listings/units/` | List units with filters (price, furnishing, etc.) |
| GET | `/api/listings/units/{id}/` | Unit detail (used by application_service) |
| GET | `/api/listings/agents/` | List agents |
| POST | `/api/listings/images/` | Bulk image upload for units |
| GET | `/api/listings/public/listings/` | Public read-only listing view (no auth needed) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `JWT_SECRET_KEY` | Yes | For JWT verification |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |

## Running Standalone

```bash
docker compose up -d db listings_service
```

## API Docs

[http://localhost:8003/api/docs/](http://localhost:8003/api/docs/)
