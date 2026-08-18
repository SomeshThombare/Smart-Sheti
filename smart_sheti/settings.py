import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# -------------------------------------------------
# Security
# -------------------------------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,.ngrok-free.app,.ngrok.io"
    ).split(",")
    if host.strip()
]


# -------------------------------------------------
# OpenRouter API
# -------------------------------------------------

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "608a757e0b829b0e65d67f3d0d930b5c231f10de3ce89c564fe3bcdca7192777")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "openai/gpt-4o")
OPENROUTER_HTTP_REFERER = os.getenv("OPENROUTER_HTTP_REFERER", "http://127.0.0.1:8000")
OPENROUTER_X_TITLE = os.getenv("OPENROUTER_X_TITLE", "Smart Sheti")

# -------------------------------------------------
# Dynamic ngrok support
# -------------------------------------------------
NGROK_URL = os.getenv("NGROK_URL", "").strip()

# Allow all ngrok domains
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".ngrok-free.app",   # ngrok free domain
    ".ngrok.io",         # older ngrok domains
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://127.0.0.1:8000",
    "https://localhost:8000",

    # Allow all ngrok URLs
    "https://*.ngrok-free.app",
    "https://*.ngrok.io",
]

# Optional: still support specific URL from env
if NGROK_URL:
    if NGROK_URL not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(NGROK_URL)


# -------------------------------------------------
# Installed Apps
# -------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "accounts.apps.AccountsConfig",

    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",

    "dashboard",
    "farmer",
    "crop",
    "fertilizer",
    "soil",
    "weather",
    "disease_detection",
    "ai_engine",
    "marketplace",
    "government_schemes",
    "equipment_rental",
    "chatbot",
    "pest_detection",
    
]


# -------------------------------------------------
# Middleware
# -------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "accounts.middleware.UserLanguageMiddleware",
    "accounts.middleware.AutoLogoutMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# -------------------------------------------------
# Authentication
# -------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "accounts.backends.UsernameEmailMobileBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_USER_MODEL = "accounts.CustomUser"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# -------------------------------------------------
# Auto Logout
# -------------------------------------------------
AUTO_LOGOUT_DELAY = 1800

AUTO_LOGOUT_EXEMPT_PATHS = [
    "/accounts/login/",
    "/accounts/logout/",
    "/accounts/send-otp/",
    "/accounts/verify-otp/",
]


# -------------------------------------------------
# URL / WSGI
# -------------------------------------------------
ROOT_URLCONF = "smart_sheti.urls"
WSGI_APPLICATION = "smart_sheti.wsgi.application"


# -------------------------------------------------
# Templates
# -------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------------------------------
# PostgreSQL Database
# -------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "smart_sheti_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "2004@Septt"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# -------------------------------------------------
# Password Validation
# -------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# -------------------------------------------------
# Internationalization
# -------------------------------------------------
LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True



LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_AGE = 1209600

# RAZORPAY_POSTMAN_TEST_MODE = True
# -------------------------------------------------
# Session / CSRF
# -------------------------------------------------
SESSION_COOKIE_AGE = 1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"


# -------------------------------------------------
# Static / Media Files
# -------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -------------------------------------------------
# Django REST Framework
# -------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


# -------------------------------------------------
# JWT
# -------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# -------------------------------------------------
# Email OTP
# -------------------------------------------------


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = "smartshetiii@gmail.com"
EMAIL_HOST_PASSWORD = "trbxbyqvogbdjcjy"   # 👈 इथे Gmail App Password टाक
EMAIL_TIMEOUT = 20
DEFAULT_FROM_EMAIL = "Smart Sheti <smartshetiii@gmail.com>"

# -------------------------------------------------
# SMS / OTP
# -------------------------------------------------
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = "+15014745725"


# -------------------------------------------------
# Admin Secret
# -------------------------------------------------
ADMIN_SECRET_CODE = os.getenv("ADMIN_SECRET_CODE", "shubham@1592")


# -------------------------------------------------
# Logging
# -------------------------------------------------
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "app.log"),
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },

    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },

    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "urllib3": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "twilio": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# -------------------------------------------------
# Razorpay
# -------------------------------------------------
RAZORPAY_KEY_ID = os.getenv(
    "RAZORPAY_KEY_ID",
    "rzp_test_SufKpZQ91tWGaR"
)

RAZORPAY_KEY_SECRET = os.getenv(
    "RAZORPAY_KEY_SECRET",
    "LkojZqAnrIh08s1uHdHAYVSM"
)

RAZORPAY_CURRENCY = os.getenv("RAZORPAY_CURRENCY", "INR")