# HomeHaven Microservices Architecture

This doc covers what each service does and why it's its own service instead of being part of a monolith.

The backend is split into 8 Django services communicating through Kafka (async events) and Nginx (sync HTTP routing). Each service owns its own database schema and can be deployed independently.

The main reason for the split: different parts of the system have very different scaling needs. Chat and notifications need WebSocket support and handle bursty real-time traffic. Listings and buildings are read-heavy with lots of filtering. Auth is security-critical and changes rarely. Keeping them separate means we can scale and deploy each one without touching the others.

---

## Auth Service
**Port:** `8001`

Handles user registration, login, and JWT token management. This is separate because auth logic is security-sensitive — we want a small, auditable codebase for anything that touches passwords and tokens. Uses SimpleJWT for token generation so we don't have to manage sessions across services.

- Issues and verifies JWTs (access + refresh tokens)
- Publishes `UserRegistered` events to Kafka
- Validates OTP status with Profile Service during login

## Profile Service
**Port:** `8002`

Manages user profiles and email verification. It's decoupled from auth because profile data (name, DOB, gender) changes frequently and has different access patterns than auth credentials. Runs its own Celery worker for sending OTP emails asynchronously.

- Stores profile data (name, DOB, gender, etc.)
- OTP generation, hashing (PBKDF2), and verification via Redis
- Celery tasks for sending verification emails

## Listings Service
**Port:** `8003`

The core real estate domain — properties, units, agents, and images. This is the most query-heavy service with complex filtering (by price, location, furnishing, etc.), so it benefits from having its own database connection pool and caching layer.

- CRUD for rental listings and units
- Search and filtering with django-filter
- Image uploads for property photos
- Produces `ListingCreated` events

## Building Service
**Port:** `8004`

Manages physical building data — addresses, amenities, floors, RERA verification. Separated from listings because a building can have many listings across different units, and the data lifecycle is different (buildings rarely change, listings come and go).

- Building metadata (address, floors, amenities like gym/pool)
- Geographic bounding box queries for map views
- Aggregated building statistics

## Application Service
**Port:** `8005`

Handles the rental application workflow. This is where the business logic lives for submitting, reviewing, and approving applications. It's separate because the approval flow is stateful and involves coordinating with multiple other services.

- Submit rental applications for specific units
- Agents can approve, reject, or hold applications
- Produces `ApplicationCreated`, `ApplicationApproved`, `ApplicationRejected` events

## Reviews Service
**Port:** `8006`

Crowdsourced ratings and reviews for buildings and agents. Separate because review data has different write patterns (append-only, rarely updated) and the aggregation logic (average ratings, counts) can be CPU-intensive.

- Submit reviews with 1-5 star ratings
- Aggregate average ratings for buildings and agents
- Produces `ReviewCreated` events

## Chat Service
**Port:** `8007`

Real-time messaging between renters and agents using Django Channels and WebSockets. This needs its own service because it runs on Daphne (ASGI) instead of Gunicorn (WSGI), and the connection model is fundamentally different — long-lived WebSocket connections vs short-lived HTTP requests.

- WebSocket endpoint: `ws://localhost:8000/ws/chat/`
- Consumes `ApplicationApproved` events to auto-create conversations
- Online presence tracking via Redis
- Rate-limited message sending
- Produces `MessageSent` events for notifications

## Notification Service
**Port:** `8008`

Central event sink that handles all system notifications. It consumes events from basically every other service and decides how to notify users (in-app, email, WebSocket push). Separate because notification logic shouldn't slow down the services producing events.

- Consumes Kafka events: `UserRegistered`, `ApplicationApproved`, `MessageSent`, `ReviewCreated`, etc.
- Real-time WebSocket push: `ws://localhost:8000/ws/notifications/`
- Async email delivery via Celery
- Notification history with read/unread tracking
- Per-user notification preferences

---

## API Documentation
Every service exposes OpenAPI 3.0 docs via `drf-spectacular`. Hit `http://localhost:<PORT>/api/docs/` for Swagger UI on any running service.
