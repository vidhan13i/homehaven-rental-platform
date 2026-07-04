"""
Django settings for notification_service.

Architecture:
  - Fully independent from all other microservices
  - Own PostgreSQL database: notification_db
  - Own Celery worker for email delivery
  - Django Channels (ASGI) for real-time WebSocket push notifications
  - Kafka consumers run in a separate management command process
  - JWT authentication uses the platform-shared JWT_SECRET_KEY (stateless)
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY ─────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required")

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ImproperlyConfigured("JWT_SECRET_KEY environment variable is required")

DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# ─── INSTALLED APPS ───────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",           # Django Channels — required for WebSocket push
    "rest_framework",
    "django_filters",
    "corsheaders",
    "notification.apps.NotificationConfig",
]

# ─── MIDDLEWARE ───────────────────────────────────────────────────────────────
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

# ─── ASGI / WSGI ─────────────────────────────────────────────────────────────
# Daphne runs the ASGI server; handles HTTP and WebSocket concurrently.
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

# ─── CHANNEL LAYERS (Redis pub/sub for WebSocket push) ────────────────────────
# Uses Redis DB 4 — distinct from chat_service (DB 3), Celery (DB 1/2), cache (DB 0)
CHANNEL_LAYERS_REDIS_URL = os.environ.get(
    "CHANNEL_LAYERS_REDIS_URL", "redis://redis:6379/4"
)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [CHANNEL_LAYERS_REDIS_URL],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# ─── REST FRAMEWORK ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "notification.authentication.http.TrustedJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "notification.api.pagination.NotificationPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept", "accept-encoding", "authorization", "content-type",
    "dnt", "origin", "user-agent", "x-csrftoken", "x-requested-with",
]

# ─── DATABASE ─────────────────────────────────────────────────────────────────
DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
if not DB_PASSWORD:
    raise ImproperlyConfigured("DB_PASSWORD environment variable is required")

DATABASES = {
    # Default postgres DB (required for Django admin sessions etc.)
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    },
    # notification_service's own isolated database
    "notification": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "notification_db",
        "USER": "postgres",
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    },
}

DATABASE_ROUTERS = ["config.db_router.NotificationRouter"]

# ─── REDIS CACHE ──────────────────────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

# ─── CELERY ───────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60
CELERY_TASK_SOFT_TIME_LIMIT = 45
CELERY_TASK_DEFAULT_QUEUE = "notifications"
CELERY_TASK_QUEUES = {
    "notifications": {},
    "email_delivery": {},
}

# ─── KAFKA ────────────────────────────────────────────────────────────────────
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_ENABLED = os.environ.get("KAFKA_ENABLED", "true").lower() == "true"
KAFKA_CONSUMER_GROUP_ID = "notification-service-consumers"

# ─── EMAIL ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Haven Rentals <noreply@haven.local>"
)

# ─── NOTIFICATION SETTINGS ────────────────────────────────────────────────────
# How long to keep offline user notifications before sending email (seconds)
NOTIFICATION_EMAIL_DELAY_SECONDS = int(
    os.environ.get("NOTIFICATION_EMAIL_DELAY_SECONDS", "300")  # 5 minutes
)
# Max notifications to return per page in API
NOTIFICATION_PAGE_SIZE = int(os.environ.get("NOTIFICATION_PAGE_SIZE", "20"))

# ─── INTERNATIONALISATION ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ─── STATIC ───────────────────────────────────────────────────────────────────
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.UUIDField"

# ─── CSRF ─────────────────────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# ─── LOGGING ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} [{process:d}] - {message}",
            "style": "{",
        },
        "kafka": {
            "format": "[KAFKA] [{levelname}] {asctime} {name} - {message}",
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
        "notification": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "kafka": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.channels": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
