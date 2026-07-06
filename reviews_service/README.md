# Reviews Service

Crowdsourced property reviews and ratings. Tenants can leave reviews for buildings they've lived in and rate their experience. The service aggregates ratings to show average scores on building listings.

## Why it's a separate service

Review data is append-only (users rarely edit reviews) and the aggregation logic (computing averages, counts, distributions) is CPU-intensive. Separating it means review queries don't compete for database connections with the listings service. It also lets us add moderation features later without touching the property data.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for review models with aggregation queries |
| djangorestframework | REST API with viewsets |
| django-filter | Filter reviews by building, agent, rating, date |
| requests + tenacity | Cross-service calls to building and profile services for validation |
| confluent-kafka | Publishes `ReviewCreated` events for notifications |
| PyJWT | JWT verification |
| drf-spectacular | API documentation |

## Directory Structure

```
reviews_service/
├── reviews/
│   ├── models/               # Review model (rating, text, building FK)
│   ├── api/
│   │   └── views.py          # ReviewViewSet with lookup and analytics endpoints
│   ├── urls.py
│   ├── management/commands/  # populate_reviews seed command
│   └── tests/
├── config/
│   ├── settings.py
│   └── db_router.py
├── Dockerfile
└── requirements.txt
```

## Key Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/api/reviews/reviews/` | List reviews with filtering |
| POST | `/api/reviews/reviews/` | Submit a new review (publishes Kafka event) |
| GET | `/api/reviews/reviews/by-building/{id}/` | All reviews for a specific building |
| GET | `/api/reviews/reviews/by-agent/{id}/` | All reviews for a specific agent |
| GET | `/api/reviews/reviews/analytics/` | Aggregate rating stats |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `JWT_SECRET_KEY` | Yes | JWT verification |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |
| `BUILDING_SERVICE_URL` | No | Defaults to `http://building_service:8000` |
| `PROFILE_SERVICE_URL` | No | Defaults to `http://profile_service:8000` |

## Running Standalone

```bash
docker compose up -d db reviews_service
```

## API Docs

[http://localhost:8006/api/docs/](http://localhost:8006/api/docs/)
