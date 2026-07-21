"""
Minimal settings.py ready to use with:
- djangorestframework
- django-cors-headers
- djangorestframework-simplejwt
- dj-database-url
- python-dotenv

Drop this into your Django project (adjust INSTALLED_APPS and other app-specific settings).
"""
from pathlib import Path
import os
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret-for-dev")
# Default to False in production unless DEBUG env explicitly set to true
DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

# ALLOWED_HOSTS can be a comma-separated list in .env
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost").split(",") if h.strip()]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",
    "rest_framework",
    
    # Your apps
    "api",
]

MIDDLEWARE = [
    # CorsMiddleware should be high up so it can add headers before responses are processed
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"  # change to your project's urls module

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]

WSGI_APPLICATION = "project.wsgi.application"  # change as needed

# Database
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Password validation (default Django validators)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (adjust for production)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Django REST Framework + Simple JWT settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Change default permission to suit your app (IsAuthenticated is common)
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Add any other Simple JWT options you need here
}

# CORS settings
# In development you can allow all origins. In production set CORS_ALLOWED_ORIGINS instead.
CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False").lower() in ("1", "true", "yes")
# Allow comma-separated origins in an env var for production
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
# If nothing specified and DEBUG is True, allow all origins for convenience
if not CORS_ALLOW_ALL_ORIGINS and not CORS_ALLOWED_ORIGINS:
    if DEBUG:
        CORS_ALLOW_ALL_ORIGINS = True

# Production security settings
if not DEBUG:
    # Ensure SECRET_KEY is overridden in production
    if SECRET_KEY == "unsafe-secret-for-dev":
        raise RuntimeError("SECRET_KEY must be set in environment for production (do not use the default).")

    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() in ("1", "true", "yes")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True").lower() in ("1", "true", "yes")
    CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "True").lower() in ("1", "true", "yes")
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() in ("1", "true", "yes")
    SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True").lower() in ("1", "true", "yes")
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
