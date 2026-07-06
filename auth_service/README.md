# Auth Service

Handles user registration, login, and JWT token management for the entire platform. This is the entry point for all user authentication — every other service trusts JWTs issued by this service.

## Why it's a separate service

Authentication is security-critical and rarely changes compared to feature services. Keeping it isolated means we can audit, patch, and deploy auth logic independently. It also keeps the User model clean — just credentials and IDs, no profile bloat.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | Handles User model, ORM, admin panel |
| djangorestframework | REST API layer with serializers and views |
| djangorestframework-simplejwt | JWT generation and validation — avoids managing sessions across services |
| django-cors-headers | CORS handling since the React frontend is on a different origin |
| psycopg2-binary | PostgreSQL driver |
| requests + tenacity | HTTP calls to profile_service with retry and exponential backoff |
| confluent-kafka | Publishes `UserRegistered` events so other services can react |
| drf-spectacular | Auto-generates OpenAPI 3.0 docs from view annotations |

## Directory Structure

```
auth_service/
├── authentication/
│   ├── models.py        # Custom User model (UUID primary key)
│   ├── serializers.py   # RegisterSerializer with validation
│   ├── views.py         # RegisterView, TokenObtainPairView (with OTP check)
│   ├── urls.py          # /register/, /login/, /token/refresh/
│   └── tests/           # API endpoint tests
├── config/
│   ├── settings.py      # Django settings (secrets from env vars)
│   ├── urls.py          # Root URL config
│   └── db_router.py     # Routes queries to auth_db
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

## Key Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| POST | `/api/auth/register/` | Creates user, sets up profile (via profile_service), triggers OTP email |
| POST | `/api/auth/login/` | Validates credentials, checks email verification, returns JWT tokens |
| POST | `/api/auth/token/refresh/` | Refreshes an expired access token |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `JWT_SECRET_KEY` | Yes | Shared across services for JWT verification |
| `DB_HOST` | No | Defaults to `localhost` |
| `DB_PORT` | No | Defaults to `5433` |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `PROFILE_SERVICE_URL` | No | Defaults to `http://profile_service:8000` |

## Running Standalone

```bash
# From the project root
docker compose up -d db auth_service
```

Or without Docker (needs a local Postgres):
```bash
cd auth_service
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

## API Docs

Once running: [http://localhost:8001/api/docs/](http://localhost:8001/api/docs/)

Export schema for Postman:
```bash
docker compose exec auth_service python manage.py spectacular --file schema.yml
```
