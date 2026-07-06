# Profile Service

Manages user profile data and handles email verification through OTP codes. When someone registers through the auth service, this is where their profile record gets created — name, date of birth, gender, etc.

## Why it's a separate service

Profile data changes much more frequently than auth credentials and has different access patterns. Users update their profiles, but their login credentials stay the same. Keeping profiles separate also means we can add new profile fields without touching the auth service at all.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for profile models, admin panel |
| djangorestframework | REST API with DRF serializers and viewsets |
| celery 5.4.0 | Sends OTP verification emails in the background so the API response isn't blocked by SMTP |
| redis / django-redis | OTP storage with automatic TTL expiration (5 min), also serves as Celery broker |
| PyJWT | Decodes JWTs from incoming requests to identify the user |
| requests + tenacity | Resilient HTTP calls to other services |
| psycopg2-binary | PostgreSQL driver |
| drf-spectacular | OpenAPI 3.0 documentation |

## Directory Structure

```
profile_service/
├── profiles_app/
│   ├── models/
│   │   └── profile.py       # Profile model (UUID pk, synced with auth)
│   ├── api/
│   │   ├── views.py          # ProfileViewSet, OTPViewSet
│   │   └── serializers.py    # Profile CRUD serializers
│   ├── tasks.py              # Celery tasks (send_otp_email)
│   ├── throttles.py          # Rate limiting for OTP requests
│   ├── management/commands/  # populate_profiles management command
│   └── tests/                # API and task tests
├── config/
│   ├── settings.py           # Settings with Redis, Celery, email config
│   ├── __init__.py           # Loads Celery app on startup
│   └── db_router.py          # Routes to profile_db
├── celery_app.py             # Celery application setup
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

## Key Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| POST | `/api/profiles/profiles/` | Create a new profile (called by auth_service during registration) |
| GET | `/api/profiles/profiles/{id}/` | Fetch a profile by UUID |
| GET | `/api/profiles/profiles/by-email/` | Lookup profile by email (used by auth during login) |
| POST | `/api/profiles/otp/request_otp/` | Generate and email a 6-digit OTP code |
| POST | `/api/profiles/otp/verify_otp/` | Verify the OTP and mark email as verified |

## How OTP works

1. A 6-digit code is generated and hashed with Django's `make_password` (PBKDF2 + salt)
2. The hash is stored in Redis with a 5-minute TTL
3. Celery sends the code via email in the background
4. When the user submits the code, it's verified with `check_password`
5. Failed attempts are tracked in Redis — lockout after 5 failures
6. On success or lockout, both the OTP and attempt counter are deleted

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `JWT_SECRET_KEY` | Yes | For decoding incoming JWTs |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |
| `REDIS_URL` | No | Defaults to `redis://redis:6379/0` |
| `CELERY_BROKER_URL` | No | Defaults to `redis://redis:6379/1` |
| `EMAIL_BACKEND` | No | Defaults to console backend for dev |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | For prod | Gmail SMTP credentials |

## Running Standalone

```bash
# Start the service with its dependencies
docker compose up -d db redis profile_service celery_worker
```

The Celery worker needs to be running alongside the service for OTP emails to actually send.

## API Docs

Once running: [http://localhost:8002/api/docs/](http://localhost:8002/api/docs/)
