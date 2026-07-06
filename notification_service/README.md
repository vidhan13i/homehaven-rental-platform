# Notification Service

Central event sink that handles all platform notifications. It consumes Kafka events from every other service and dispatches notifications through multiple channels — in-app alerts, WebSocket push, and email.

## Why it's a separate service

Notification logic should never slow down the services that produce events. If sending an email takes 3 seconds, that shouldn't block the application approval API response. This service runs its own consumers and workers independently. It also centralizes all notification preferences and history in one place.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for notification and preference models |
| channels 4.2.2 | WebSocket support for real-time push notifications |
| channels-redis | Redis channel layer for broadcasting to connected clients |
| daphne 4.1.2 | ASGI server for HTTP + WebSocket |
| celery 5.4.0 | Async email delivery with retry (exponential backoff on SMTP failures) |
| redis / django-redis | Celery broker + cache |
| confluent-kafka | Consumes events from all domain topics |
| requests + tenacity | Cross-service calls (e.g., fetching user email from profile service) |
| drf-spectacular | API documentation |

## Directory Structure

```
notification_service/
├── notification/
│   ├── models/
│   │   ├── notification.py        # Notification model with idempotency key
│   │   └── preference.py          # Per-user channel preferences (in-app, email, push, SMS)
│   ├── consumers/
│   │   ├── auth_consumer.py       # Handles UserRegistered events
│   │   ├── application_consumer.py # Handles ApplicationCreated/Approved/Rejected
│   │   ├── message_consumer.py    # Handles MessageSent events
│   │   ├── review_consumer.py     # Handles ReviewCreated events
│   │   └── listing_consumer.py    # Handles ListingCreated events
│   ├── services/
│   │   └── notification_service.py # Core dispatch logic (store → push → email)
│   ├── tasks/
│   │   └── email_tasks.py         # Celery tasks for email delivery
│   ├── api/
│   │   └── views.py               # REST endpoints for notification history
│   └── ws/                        # WebSocket consumer for push notifications
├── config/
│   ├── settings.py
│   ├── asgi.py
│   └── db_router.py
├── celery_app.py
├── Dockerfile
└── requirements.txt
```

## Key Endpoints

### REST API
| Method | Path | What it does |
|--------|------|-------------|
| GET | `/api/notifications/` | Paginated notification history for the authenticated user |
| POST | `/api/notifications/{id}/read/` | Mark a notification as read |
| POST | `/api/notifications/read-all/` | Mark all notifications as read |
| GET | `/api/notifications/preferences/` | Get user's notification preferences |
| PUT | `/api/notifications/preferences/` | Update preferences |

### WebSocket
| Protocol | Path | What it does |
|----------|------|-------------|
| WS | `ws://localhost:8000/ws/notifications/` | Real-time push notifications |

## How notification dispatch works

1. Kafka consumer receives an event (e.g., `ApplicationApproved`)
2. Check the target user's notification preferences
3. Store the notification in the database (with `source_event_id` for idempotency — prevents duplicates if Kafka redelivers)
4. If the user is online, push via WebSocket
5. If email notifications are enabled, queue a Celery task for email delivery
6. Email task retries with exponential backoff (1min → 2min → 4min) on SMTP failures

## Kafka Topics Consumed

| Topic | Source | What triggers it |
|-------|--------|-----------------|
| `UserRegistered` | auth_service | New user registration |
| `ApplicationCreated` | application_service | New rental application |
| `ApplicationApproved` | application_service | Agent approves application |
| `ApplicationRejected` | application_service | Agent rejects application |
| `MessageSent` | chat_service | New chat message (for offline users) |
| `ReviewCreated` | reviews_service | New review submitted |
| `ListingCreated` | listings_service | New listing published |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `JWT_SECRET_KEY` | Yes | JWT verification |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |
| `REDIS_URL` | No | Cache and channel layer |
| `CELERY_BROKER_URL` | No | Task queue broker |
| `KAFKA_BOOTSTRAP_SERVERS` | No | Kafka broker address |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | For prod | SMTP credentials |

## Running Standalone

```bash
docker compose up -d db redis kafka notification_service
```

Needs Redis for WebSocket channel layer and Kafka for event consumption.

## API Docs

[http://localhost:8008/api/docs/](http://localhost:8008/api/docs/)
