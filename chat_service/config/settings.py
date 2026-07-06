"""
Django settings for chat_service.

Follows the exact same patterns as all other services in this platform:
  - JWT_SECRET_KEY from environment (shared secret, stateless auth)
  - Separate PostgreSQL database (chat_db) with a DB router
  - Redis for Celery broker/result AND Django Channel Layer (separate DBs)
  - REST_FRAMEWORK with TrustedJWTAuthentication
  - CORS, TIME_ZONE, ALLOWED_HOSTS from .env

Additions unique to chat_service:
  - CHANNEL_LAYERS: Redis backend for Django Channels
  - ASGI_APPLICATION (instead of WSGI_APPLICATION for WebSocket support)
  - Daphne runs the ASGI server (see Dockerfile CMD)
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ImproperlyConfigured("JWT_SECRET_KEY environment variable is required")

DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,gateway,chat_service").split(",")

INSTALLED_APPS = [
    "drf_spectacular",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",  # Django Channels — must be before app
    "rest_framework",
    "django_filters",
    "corsheaders",
    "chat.apps.ChatConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ASGI_APPLICATION is set so Django Channels wraps the ASGI app with its router.
# Daphne reads config.asgi:application and routes HTTP vs WebSocket accordingly.
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

# Uses Redis DB 3 — distinct from Celery broker (DB 1) and result backend (DB 2).
# Every chat_service replica connects to the same Redis Channel Layer, which means
# a message sent on replica A is broadcast to all clients on replica B as well.
# This is how horizontal scaling works for WebSocket services.
CHANNEL_LAYERS_REDIS_URL = os.environ.get(
    "CHANNEL_LAYERS_REDIS_URL", "redis://redis:6379/3"
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [CHANNEL_LAYERS_REDIS_URL],
            "capacity": 1500,  # Max messages queued per channel
            "expiry": 10,  # Seconds before an undelivered message expires
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "chat.authentication.http.TrustedJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "chat.api.pagination.ChatPagination",
    "PAGE_SIZE": 30,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",
        "user": "600/hour",
    },
}

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:8000"
).split(",")
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
if not DB_PASSWORD:
    raise ImproperlyConfigured("DB_PASSWORD environment variable is required")

DATABASES = {
    # Default postgres DB (required for Django admin, content types, sessions)
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    },
    # chat_service's own isolated database
    "chat": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "chat_db",
        "USER": "postgres",
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    },
}

DATABASE_ROUTERS = ["config.db_router.ChatRouter"]

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "IGNORE_EXCEPTIONS": False,
        },
    }
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30
CELERY_TASK_SOFT_TIME_LIMIT = 20
CELERY_TASK_DEFAULT_QUEUE = "chat_notifications"

LISTINGS_SERVICE_URL = os.environ.get(
    "LISTINGS_SERVICE_URL", "http://listings_service:8000"
)
APPLICATION_SERVICE_URL = os.environ.get(
    "APPLICATION_SERVICE_URL", "http://application_service:8000"
)
PROFILE_SERVICE_URL = os.environ.get(
    "PROFILE_SERVICE_URL", "http://profile_service:8000"
)

# Presence TTL: Redis key expires after this many seconds if no heartbeat
CHAT_PRESENCE_TTL_SECONDS = int(os.environ.get("CHAT_PRESENCE_TTL_SECONDS", "35"))
# Heartbeat interval: client must send heartbeat every N seconds
CHAT_HEARTBEAT_INTERVAL_SECONDS = int(
    os.environ.get("CHAT_HEARTBEAT_INTERVAL_SECONDS", "30")
)
# Rate limiting: max messages in the time window
CHAT_RATE_LIMIT_MAX_MESSAGES = int(os.environ.get("CHAT_RATE_LIMIT_MAX_MESSAGES", "10"))
CHAT_RATE_LIMIT_WINDOW_SECONDS = int(
    os.environ.get("CHAT_RATE_LIMIT_WINDOW_SECONDS", "5")
)
# Max message length in characters
CHAT_MESSAGE_MAX_LENGTH = int(os.environ.get("CHAT_MESSAGE_MAX_LENGTH", "4000"))
# Max attachment size in bytes (10 MB)
CHAT_MAX_ATTACHMENT_SIZE = int(
    os.environ.get("CHAT_MAX_ATTACHMENT_SIZE", str(10 * 1024 * 1024))
)

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Haven Rentals <noreply@haven.local>"
)

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} - {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "chat": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "django.channels": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Chat Service API",
    "DESCRIPTION": """Real-time chat functionality between users. 

### WebSockets API

**Endpoint**: `ws://localhost:8000/ws/chat/?token=<JWT>`

**Authentication**: Pass JWT token in query parameter.

**Incoming Events**:
- `chat_message`: Send a message to a conversation.

**Outgoing Events**:
- `chat_message`: Received when a message is sent to a conversation you are in.""",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
}
