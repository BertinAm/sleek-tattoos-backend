"""
Django settings for the Sleek Tattoos API.

Config is environment-driven (see .env.example) so the same codebase runs
locally against SQLite and in production against MySQL on Namecheap Stellar
without code changes — only the .env file differs.
"""
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
# .env lives next to manage.py; safe to skip silently if absent (e.g. prod
# envs that inject real environment variables instead of a file).
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='insecure-dev-key-change-me')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Fail loudly rather than silently shipping the dev key to production — a
# leaked/guessable SECRET_KEY breaks session signing, password reset tokens,
# and (via simplejwt, which by default doesn't use SECRET_KEY but easily
# could if reconfigured) auth entirely.
if not DEBUG and SECRET_KEY == 'insecure-dev-key-change-me':
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY must be set to a real secret when DJANGO_DEBUG=False. '
        'Generate one with: python -c "from django.core.management.utils import '
        'get_random_secret_key; print(get_random_secret_key())"'
    )

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',

    'core',
    'content',
    'bookings',
    'contacts',
    'support',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# --- Database ---------------------------------------------------------------
# No DATABASE_URL -> local SQLite (zero setup for development).
# DATABASE_URL set  -> whatever it points to (MySQL in production).
DATABASE_URL = env('DATABASE_URL', default='')
if DATABASE_URL:
    DATABASES = {'default': env.db('DATABASE_URL')}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = env('DJANGO_TIME_ZONE', default='Asia/Kolkata')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = env('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- DRF / JWT ---------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    # Blanket safety net on every endpoint (bumped comfortably above normal
    # browsing/admin-panel traffic — a single dashboard load alone fires ~8
    # requests). 'login' and 'public_write' below are the real limiters on
    # the endpoints that actually need strict throttling; see individual
    # views for where those scopes are applied.
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',
        'user': '3000/hour',
        'login': '5/min',
        'public_write': '20/min',
    },
}

# Multipart upload ceiling — matches ImageUploadSerializer's 5MB image-size
# check (core/serializers.py) with headroom for multipart overhead. Also
# caps non-file POST bodies at the same size, which is generous for JSON
# booking/contact/support payloads but still bounds them against abuse.
DATA_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_LIFETIME_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_LIFETIME_DAYS', default=14)),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# --- CORS ---------------------------------------------------------------
# The frontend (sleektattoos.com) and API (api.sleektattoos.com) are
# different origins, so every browser request needs an explicit allow-list —
# there is no shared-cookie trust between them by default.
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000'])
CORS_ALLOW_CREDENTIALS = True
# django-cors-headers' default allow-list doesn't include our custom visitor
# identity header (frontend/lib/api.js sends X-Visitor-Token on every support
# chat request) — without this, the browser's preflight rejects it silently
# (looks like a generic network failure client-side, not an obvious CORS error).
from corsheaders.defaults import default_headers  # noqa: E402
CORS_ALLOW_HEADERS = list(default_headers) + ['x-visitor-token']

# --- Google Calendar (service account) ---------------------------------------
GOOGLE_SERVICE_ACCOUNT_FILE = env('GOOGLE_SERVICE_ACCOUNT_FILE', default='')
GOOGLE_CALENDAR_OWNER_EMAIL = env('GOOGLE_CALENDAR_OWNER_EMAIL', default='')

# --- Email (Namecheap-hosted mailboxes, cPanel mail) --------------------------
# Two separate real mailboxes, two separate purposes — see core/emailing.py for
# why this isn't just one connection with a spoofed "From" header:
#   hello@sleektattoos.com   -> booking notifications
#   noreply@sleektattoos.com -> system notifications (admin login alerts)
# Same host/port for both (same domain, same mail server). Port 465 is
# implicit SSL, not STARTTLS, hence USE_SSL not USE_TLS (Django errors if
# both are set).
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='sleektattoos.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)
EMAIL_USE_TLS = False

EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='hello@sleektattoos.com')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

NOREPLY_EMAIL_HOST_USER = env('NOREPLY_EMAIL_HOST_USER', default='noreply@sleektattoos.com')
NOREPLY_EMAIL_HOST_PASSWORD = env('NOREPLY_EMAIL_HOST_PASSWORD', default='')

# Where booking and admin-login notification emails actually get sent.
STUDIO_NOTIFICATION_EMAIL = env('STUDIO_NOTIFICATION_EMAIL', default='sleektattoos00@gmail.com')

AUTH_USER_MODEL = 'auth.User'

# --- Production security hardening -------------------------------------------
# All gated on DEBUG so local HTTP dev (no TLS) keeps working unmodified —
# these assume the production deploy sits behind Namecheap/Cloudflare TLS.
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    X_FRAME_OPTIONS = 'DENY'
    # 1 year, standard HSTS baseline — only turn on once HTTPS is confirmed
    # working end-to-end (an HSTS mistake locks out plain-HTTP access for as
    # long as the max-age, so this isn't safe to flip on blind).
    SECURE_HSTS_SECONDS = env.int('DJANGO_HSTS_SECONDS', default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Django's own /admin/ site uses session+CSRF cookies (unlike the JWT API);
    # the frontend origin needs to be trusted for any state-changing request
    # made against it (e.g. logging into /admin/ from a browser).
    CSRF_TRUSTED_ORIGINS = env.list('DJANGO_CSRF_TRUSTED_ORIGINS', default=[])
