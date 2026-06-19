"""
Django settings for profile_service.
"""
from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY environment variable is required")

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    raise ImproperlyConfigured("JWT_SECRET_KEY environment variable is required")

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,profile_service,gateway').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'profiles_app.apps.ProfilesAppConfig',
    'rest_framework',
    'django_filters',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# JWT_SECRET_KEY is validated above

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'common.authentication.TrustedJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Rate limiting — applied per-view via throttle_classes
    'DEFAULT_THROTTLE_RATES': {
        'otp_request': '5/hour',   # max 5 OTP requests per IP per hour
        'otp_verify': '10/hour',   # max 10 verify attempts per IP per hour
    },
}

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:8000',
]

# ─── INTER-SERVICE URLs ────────────────────────────────────────────────────────
BUILDING_SERVICE_URL = os.environ.get('BUILDING_SERVICE_URL', 'http://building_service:8000')
LISTINGS_SERVICE_URL = os.environ.get('LISTINGS_SERVICE_URL', 'http://listings_service:8000')
REVIEWS_SERVICE_URL  = os.environ.get('REVIEWS_SERVICE_URL',  'http://reviews_service:8000')

# ─── DATABASE ──────────────────────────────────────────────────────────────────
DB_HOST     = os.environ.get('DB_HOST',     'localhost')
DB_PORT     = os.environ.get('DB_PORT',     '5432')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
if not DB_PASSWORD:
    raise ImproperlyConfigured("DB_PASSWORD environment variable is required")

DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     "postgres",
        "USER":     "postgres",
        "PASSWORD": DB_PASSWORD,
        "HOST":     DB_HOST,
        "PORT":     DB_PORT,
    },
    "profiles_app": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     "profiles_app",
        "USER":     "postgres",
        "PASSWORD": DB_PASSWORD,
        "HOST":     DB_HOST,
        "PORT":     DB_PORT,
    },
}

DATABASE_ROUTERS = ["config.db_router.ProfilesRouter"]

# ─── REDIS ─────────────────────────────────────────────────────────────────────
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'IGNORE_EXCEPTIONS': False,
        },
    }
}

# ─── CELERY ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL        = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/1')
CELERY_RESULT_BACKEND    = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Asia/Kolkata'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT   = 30   # hard kill task after 30s
CELERY_TASK_SOFT_TIME_LIMIT = 20  # raise SoftTimeLimitExceeded after 20s

# ─── EMAIL ─────────────────────────────────────────────────────────────────────
# Use SMTP in prod; console backend in dev when EMAIL_BACKEND is not set
EMAIL_BACKEND  = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'   # prints to stdout in dev
)
EMAIL_HOST         = os.environ.get('EMAIL_HOST',         'smtp.gmail.com')
EMAIL_PORT         = int(os.environ.get('EMAIL_PORT',     '587'))
EMAIL_USE_TLS      = os.environ.get('EMAIL_USE_TLS',      'True') == 'True'
EMAIL_HOST_USER    = os.environ.get('EMAIL_HOST_USER',    '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Haven Rentals <noreply@haven.local>')

# ─── OTP CONFIG ────────────────────────────────────────────────────────────────
OTP_EXPIRY_SECONDS = int(os.environ.get('OTP_EXPIRY_SECONDS', '300'))  # 5 minutes
OTP_REDIS_KEY_PREFIX = 'otp'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
