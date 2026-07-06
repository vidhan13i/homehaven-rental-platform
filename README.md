# HomeHaven — Django Microservices Rental Platform

[![Python Version](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/Django-6.0.2-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-Enforced-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis Cache](https://img.shields.io/badge/Redis-7--alpine-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Celery Task Queue](https://img.shields.io/badge/Celery-5.4.0-37814A?style=flat-square&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Nginx Gateway](https://img.shields.io/badge/Nginx-Gateway-009639?style=flat-square&logo=nginx&logoColor=white)](https://nginx.org/)
[![Tenacity Resilience](https://img.shields.io/badge/Tenacity-Resilient-orange?style=flat-square)](https://tenacity.readthedocs.io/)
[![OpenAPI 3.0](https://img.shields.io/badge/OpenAPI-3.0-85EA2D?style=flat-square&logo=openapi-initiative&logoColor=black)](https://www.openapis.org/)
[![Swagger UI](https://img.shields.io/badge/Swagger-UI-85EA2D?style=flat-square&logo=swagger&logoColor=black)](https://swagger.io/)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=flat-square&logo=apache-kafka&logoColor=white)](https://kafka.apache.org/)
[![CI Pipeline](https://github.com/vidhan13i/rental-mvc-proejct/actions/workflows/ci.yml/badge.svg)](https://github.com/vidhan13i/rental-mvc-proejct/actions)

HomeHaven is a crowdsourced tenant reviews, building ratings, and rental applications platform. It's built as a set of independent Django REST Framework microservices behind an Nginx API gateway, with a React frontend handling the UI. The goal was to learn how to properly decompose a monolith into services that can be deployed and scaled independently.

---

## System Architecture

The whole platform runs on a single Docker bridge network (`rental_network`). Services find each other by container name — no service registry needed since everything is on the same compose network. Nginx sits at the front and routes requests to the right service based on URL prefix.

```mermaid
graph TD
    Client([User Browser]) -->|HTTP :8000| Gateway[Nginx API Gateway]

    subgraph Services [Backend Microservices]
        Gateway --> Auth
        Gateway --> Profile
        Gateway --> Listings
        Gateway --> Building
        Gateway --> Applications
        Gateway --> Reviews
        Gateway --> Chat
        Gateway --> Notifications
    end

    subgraph Event-Driven Bus [Apache Kafka]
        Auth -.->|Produce| Events[Topics]
        Applications -.->|Produce| Events
        Reviews -.->|Produce| Events
        Listings -.->|Produce| Events
        
        Events -.->|Consume| Chat
        Events -.->|Consume| Notifications
    end

    subgraph Data & Queue [Databases]
        Services === PG[(PostgreSQL)]
        Chat & Notifications & Profile === Redis[(Redis Broker)]
    end
```

### Why these technologies?

- **Django REST Framework** — I wanted something batteries-included where I wouldn't have to write auth middleware or request parsing from scratch. DRF's serializers, viewsets, and permission classes save a lot of boilerplate, and `drf-spectacular` auto-generates OpenAPI docs from the code.
- **PostgreSQL** — Standard choice for relational data. Each service gets its own logical database on a shared Postgres instance (in prod you'd split these out to separate servers).
- **Apache Kafka** — The services need to react to events without tight coupling. When someone submits an application, the notification service and chat service both need to know, but the application service shouldn't have to call them directly. Kafka handles that fan-out. We went with Confluent's Docker images (`cp-kafka:7.6.1`) after running into issues with Bitnami's `latest` tag missing `kafka-topics.sh` for healthchecks.
- **Redis** — Used for three different things: Celery broker (task queues), Django Channels layer (WebSocket pub/sub), and OTP storage with TTL. Each use case gets its own Redis DB number to avoid key collisions.
- **Celery** — Sending emails synchronously would block the request thread. Celery offloads that to a worker process. Same deal for any slow background work.
- **Nginx** — Acts as the API gateway. It handles routing, CORS, and serves as the single entry point so the frontend only needs to know about one host.
- **Tenacity** — When service A calls service B over HTTP, B might be temporarily down. Tenacity gives us retry with exponential backoff so transient failures don't immediately crash the whole flow. The alternative was writing retry loops by hand, which gets messy fast.

### Event-Driven Communication

- **Notification Service** consumes events from Kafka (`UserRegistered`, `ApplicationCreated`, `ApplicationApproved`, `ApplicationRejected`, `MessageSent`, `ReviewCreated`, `ListingCreated`) and dispatches WebSocket alerts and emails.
- **Chat Service** listens for `ApplicationApproved` events and auto-creates a conversation between the renter and agent so they can start messaging immediately.

### Services Overview

| # | Service | What it does |
|---|---------|-------------|
| 1 | **Nginx Gateway** | Single entry point, routes by URL prefix |
| 2 | **Auth Service** | Registration, JWT tokens (SimpleJWT), coordinates profile creation |
| 3 | **Profile Service** | User profiles, OTP email verification |
| 4 | **Celery Workers** | Background email dispatch for OTP codes |
| 5 | **Application Service** | Rental application lifecycle (create, approve, reject) |
| 6 | **Listings Service** | Properties, units, agents, images |
| 7 | **Building Service** | Buildings, amenities, RERA verification |
| 8 | **Reviews Service** | Crowdsourced property ratings and tenant feedback |
| 9 | **Chat Service** | Real-time messaging via Django Channels + WebSockets |
| 10 | **Notification Service** | Event-driven notifications (in-app, email, WebSocket push) |

---

## API Documentation (OpenAPI 3.0)

Every service has its own Swagger UI and ReDoc. Once the containers are running:

| Service | Swagger UI | ReDoc |
|---------|------------|-------|
| Auth Service | [http://localhost:8001/api/docs/](http://localhost:8001/api/docs/) | [http://localhost:8001/api/redoc/](http://localhost:8001/api/redoc/) |
| Profile Service | [http://localhost:8002/api/docs/](http://localhost:8002/api/docs/) | [http://localhost:8002/api/redoc/](http://localhost:8002/api/redoc/) |
| Listings Service | [http://localhost:8003/api/docs/](http://localhost:8003/api/docs/) | [http://localhost:8003/api/redoc/](http://localhost:8003/api/redoc/) |
| Building Service | [http://localhost:8004/api/docs/](http://localhost:8004/api/docs/) | [http://localhost:8004/api/redoc/](http://localhost:8004/api/redoc/) |
| Application Service| [http://localhost:8005/api/docs/](http://localhost:8005/api/docs/) | [http://localhost:8005/api/redoc/](http://localhost:8005/api/redoc/) |
| Reviews Service | [http://localhost:8006/api/docs/](http://localhost:8006/api/docs/) | [http://localhost:8006/api/redoc/](http://localhost:8006/api/redoc/) |
| Chat Service | [http://localhost:8007/api/docs/](http://localhost:8007/api/docs/) | [http://localhost:8007/api/redoc/](http://localhost:8007/api/redoc/) |
| Notification Service| [http://localhost:8008/api/docs/](http://localhost:8008/api/docs/) | [http://localhost:8008/api/redoc/](http://localhost:8008/api/redoc/) |

You'll need to pass `Bearer <JWT>` in the Swagger UI Authorize button for protected endpoints.

---

## Platform Workflows

These diagrams show the actual request flows through the system — useful for understanding how the services coordinate.

### User Registration & Profile Setup

When someone registers, the auth service creates the user locally, then calls the profile service to set up their profile. If the profile service is down, we roll back the user creation to avoid orphaned accounts. After that, an OTP is generated and emailed via Celery.

```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'primaryColor': '#009688', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#f3f4f6'}}}%%
sequenceDiagram
    autonumber
    actor User as User Browser
    participant Gate as Nginx Gateway
    participant Auth as Auth Service
    participant Prof as Profile Service
    participant Red as Redis Cache
    participant Cel as Celery Worker

    User->>Gate: POST /api/auth/register/
    Gate->>Auth: Forward registration request
    Auth->>Auth: Validate serializer & save Auth User (DB)
    
    rect rgb(240, 248, 255)
        Note over Auth, Prof: Profile creation with retry
        Auth->>Prof: POST /api/profiles/profiles/ (make_resilient_request)
        alt Profile Success
            Prof-->>Auth: 201 Created (Profile DB record saved)
        else Transient Failure / Timeout (Attempts Exhausted)
            Prof--xAuth: Connection Error / Timeout
            Auth->>Auth: Delete Auth User (DB Rollback)
            Auth-->>Gate: 503 Service Unavailable
            Gate-->>User: {"message": "Profile service temporarily unavailable"}
        end
    end

    rect rgb(255, 240, 245)
        Note over Auth, Prof: OTP request with retry
        Auth->>Prof: POST /api/profiles/otp/request_otp/ (make_resilient_request)
        Prof->>Prof: Generate 6-digit OTP code
        Prof->>Prof: Hash code using make_password (PBKDF2)
        Prof->>Red: Store hash in Redis (Key: otp:{email}, TTL: 5 min)
        Prof->>Cel: Trigger send_otp_email.delay(email, otp)
        Prof-->>Auth: 200 OK
        Auth-->>Gate: 201 Created
        Gate-->>User: {"message": "OTP sent successfully. Please verify your email."}
    end

    Cel->>Cel: Fetch email credentials & connect to SMTP
    Cel-->>User: Send Plaintext Email containing 6-digit OTP
```

### OTP Verification

Before logging in, users must verify their email with the 6-digit code. There's a brute-force lockout after 5 failed attempts — since the code space is small (6 digits), we need to rate-limit guesses.

```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'primaryColor': '#3b82f6', 'primaryTextColor': '#ffffff', 'lineColor': '#2563eb'}}}%%
flowchart TD
    Start([User submits 6-digit OTP & email]) --> Request[POST /api/profiles/otp/verify_otp/]
    Request --> CheckLock{Attempts key in Redis >= 5?}
    
    CheckLock -- Yes --> Lockout[Delete OTP & Attempts keys from Redis] --> FailLock[Return 400: Invalid or expired OTP]
    CheckLock -- No --> FetchHash[Fetch OTP hash from Redis]
    
    FetchHash --> CheckHash{Stored Hash exists & check_password matches?}
    CheckHash -- Yes --> VerifySuccess[Set is_email_verified = True on Profile DB]
    VerifySuccess --> ClearRedis[Delete OTP & Attempts keys from Redis]
    ClearRedis --> Success[Return 200: Email verified successfully]
    
    CheckHash -- No --> IncAttempts[Increment Attempts key in Redis]
    IncAttempts --> CheckMax{Attempts >= 5?}
    CheckMax -- Yes --> Lockout
    CheckMax -- No --> FailAttempt[Return 400: Invalid or expired OTP]
```

### Login & JWT Issuance

The auth service validates credentials with SimpleJWT, then checks with the profile service whether the email is verified before handing out tokens.

```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'primaryColor': '#8b5cf6', 'tertiaryColor': '#f3f4f6'}}}%%
sequenceDiagram
    autonumber
    actor User as User Browser
    participant Gate as Nginx Gateway
    participant Auth as Auth Service
    participant Prof as Profile Service

    User->>Gate: POST /api/auth/login/
    Gate->>Auth: Forward login credentials
    Auth->>Auth: Validate username & password
    Auth->>Prof: GET /api/profiles/profiles/by-email/?email=x (make_resilient_request)
    
    alt Profile Down (Attempts Exhausted)
        Prof--xAuth: Connection Error / Timeout
        Auth-->>Gate: 503 Service Unavailable (Graceful Error response)
        Gate-->>User: {"message": "Profile service temporarily unavailable"}
    else Profile Successful & Email Verified
        Prof-->>Auth: 200 OK (is_email_verified = True)
        Auth->>Auth: Generate Access & Refresh JWT Tokens
        Auth-->>Gate: 200 OK (Returns JWT tokens)
        Gate-->>User: Token payload
    else Profile Successful but Email Unverified
        Prof-->>Auth: 200 OK (is_email_verified = False)
        Auth-->>Gate: 400 Bad Request
        Gate-->>User: {"detail": "Email not verified. Please verify your OTP."}
    end
```

### Rental Application Flow

When fetching an application, the application service fans out to listings, building, and profile services in parallel to assemble the full picture.

```mermaid
%%{init: {'theme': 'default', 'themeVariables': { 'primaryColor': '#f59e0b', 'tertiaryColor': '#fef3c7'}}}%%
sequenceDiagram
    autonumber
    actor Applicant as Tenant Browser
    participant Gate as Nginx Gateway
    participant App as Application Service
    participant List as Listings Service
    participant Build as Building Service
    participant Prof as Profile Service

    Applicant->>Gate: GET /api/applications/applications/{id}/
    Gate->>App: Route application fetch
    App->>App: Retrieve application data from DB
    
    par Query Unit Details
        App->>List: GET /api/listings/units/{unit_id}/ (make_resilient_request)
        List-->>App: Unit & Listing Data
    and Query Building Details
        App->>Build: GET /api/buildings/buildings/{building_id}/ (make_resilient_request)
        Build-->>App: Building info (verify address, pin, RERA status)
    and Query Tenant Profile
        App->>Prof: GET /api/profiles/profiles/{profile_id}/ (make_resilient_request)
        Prof-->>App: Tenant profile details
    end

    App-->>Gate: 200 OK (Complete Aggregated Application Info)
    Gate-->>Applicant: Aggregate JSON response
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose installed.

### Setup
1. Clone the repo and `cd` into it:
   ```bash
   cd Rental_mvc_project
   ```

2. Create your `.env` from the template:
   ```bash
   cp .env.example .env
   ```
   Fill in `DB_PASSWORD`, `JWT_SECRET_KEY`, `EMAIL_HOST_PASSWORD`, and any other blanks.

3. Build and start everything:
   ```bash
   docker compose up -d --build
   ```

4. Access points:
   - **API Gateway**: `http://localhost:8000/`
   - **Frontend**: `http://localhost:5174/`
   - **Health Check**: `http://localhost:8000/health/`

---

## Security & Fault Tolerance Notes

These are changes made during development that are worth knowing about:

### Secrets handling
All secrets (JWT keys, DB passwords, SMTP creds) used to be hardcoded in settings files. They've been moved to environment variables loaded from `.env`. Each service validates on startup that its required secrets are present — if something's missing, Django raises `ImproperlyConfigured` and the container fails immediately rather than running in a broken state.

### OTP hashing
OTPs were originally hashed with plain SHA-256. The problem is that a 6-digit code has only a million possibilities, so SHA-256 hashes are trivially reversible with a lookup table. We switched to Django's `make_password`/`check_password` which uses PBKDF2 with a random salt. Combined with the 5-attempt lockout and automatic key deletion, this makes brute-forcing impractical.

### Inter-service resilience
When one service calls another over HTTP, there's always a chance the target is down or slow. Without timeouts, the calling thread just hangs forever. We added a shared resilience library (`shared_lib/resilience.py`) that wraps `requests` calls with Tenacity retry logic — exponential backoff, filtered retries (only on `ConnectionError`, `Timeout`, and 5xx responses), and strict timeout constraints. If retries are exhausted, the caller returns a clean `503` response instead of crashing.

---

## Known Issues & Fixes

Some bugs we hit during development that were tricky to debug:

### Agent couldn't see applications for their properties
The application queryset was filtering by `user == application.owner`, but agents aren't the "owner" of an application — the renter is. Fixed it to look up the agent's units from the listings service, then filter applications by those unit IDs.

### Profile IDs were out of sync
The profile service was ignoring the UUID sent from auth and generating its own. This meant `Auth.id != Profile.id`, which broke cross-service lookups. Fixed the serializer to accept and use the auth-provided UUID.

### Chat messages showing up upside down
The API was returning messages oldest-first, but the frontend was prepending them. Fixed the API to return `-created_at` ordering and adjusted the React flex layout.

### Double messages in chat
A race condition — the WebSocket broadcast was faster than the REST API response, so the frontend would add the message from the WebSocket, then add it again from the API callback. Added a duplicate ID check in the frontend's API handler.

### Users showing as offline when they were online
The WebSocket consumer was broadcasting `user_online` when someone connected, but it never told newly-connecting users about people already in the room. Fixed by querying Redis for the other participant's presence during the connection handshake.

---

## Performance (Benchmarked)

We benchmarked the system locally using Docker Compose. Full details in [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md).

- **API Throughput**: Peaks at ~2,280 req/sec for cached endpoints, ~1,100 req/sec for complex DB joins.
- **WebSocket**: 0% failure rate at 250 concurrent users, 45ms average latency.
- **Kafka**: 14,000+ messages/sec producer throughput.
- **Docker**: Cold start ~105s, warm start ~15s.
