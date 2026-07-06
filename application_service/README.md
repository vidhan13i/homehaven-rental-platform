# Application Service

Handles the rental application lifecycle — tenants submit applications for units, and agents can approve, reject, or hold them. This is where the core business workflow lives.

## Why it's a separate service

The application flow is stateful and involves coordinating with multiple services (listings for unit data, building for address verification, profile for tenant info). It also publishes events that trigger downstream actions in chat and notification services. Keeping this separate means application logic can evolve independently from the property data models.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for application, applicant, and document models |
| djangorestframework | REST API with viewsets |
| django-filter | Filter applications by status, unit, date |
| requests + tenacity | Cross-service HTTP calls with retry (to listings, building, profile) |
| confluent-kafka | Publishes `ApplicationCreated`, `ApplicationApproved`, `ApplicationRejected` events |
| PyJWT | JWT verification |
| drf-spectacular | API documentation |

## Directory Structure

```
application_service/
├── application/
│   ├── models/               # Application, Applicant, Document models
│   ├── api/
│   │   ├── views.py          # ApplicationViewSet with approve/reject actions
│   │   └── serializers.py    # Nested serializers for applications
│   ├── urls.py
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
| GET | `/api/applications/applications/` | List applications (filtered by role — renters see theirs, agents see applications for their units) |
| POST | `/api/applications/applications/` | Submit a new application |
| GET | `/api/applications/applications/{id}/` | Full application detail with aggregated data from listings, building, and profile services |
| POST | `/api/applications/applications/{id}/approve/` | Agent approves (triggers Kafka event → chat room creation + notification) |
| POST | `/api/applications/applications/{id}/reject/` | Agent rejects |

## How the approval flow works

1. Tenant submits an application for a unit
2. `ApplicationCreated` event is published → notification service alerts the agent
3. Agent reviews and calls `/approve/`
4. `ApplicationApproved` event is published → chat service auto-creates a conversation between tenant and agent, notification service alerts the tenant

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `JWT_SECRET_KEY` | Yes | JWT verification |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |
| `LISTINGS_SERVICE_URL` | No | Defaults to `http://listings_service:8000` |
| `BUILDING_SERVICE_URL` | No | Defaults to `http://building_service:8000` |
| `PROFILE_SERVICE_URL` | No | Defaults to `http://profile_service:8000` |

## Running Standalone

```bash
docker compose up -d db application_service
```

## API Docs

[http://localhost:8005/api/docs/](http://localhost:8005/api/docs/)
