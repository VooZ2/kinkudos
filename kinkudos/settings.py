import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent
APP_VERSION = os.environ.get("KINKUDOS_APP_VERSION", "26.5.0")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def secret_value(name, default=""):
    file_name = os.environ.get(f"{name}_FILE")
    if file_name:
        return Path(file_name).read_text(encoding="utf-8").strip()
    return os.environ.get(name, default)


DEBUG = env_bool("KINKUDOS_DEBUG", True)
SECRET_KEY = secret_value("KINKUDOS_SECRET_KEY", "development-only-change-me")
if not DEBUG and SECRET_KEY == "development-only-change-me":
    raise RuntimeError("KINKUDOS_SECRET_KEY arba KINKUDOS_SECRET_KEY_FILE privalomas gamyboje")

ALLOWED_HOSTS = env_list("KINKUDOS_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list(
    "KINKUDOS_CSRF_TRUSTED_ORIGINS",
    "",
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "economy.apps.EconomyConfig",
]

MIDDLEWARE = [
    "economy.middleware.TrustedProxyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "economy.middleware.SetupRequiredMiddleware",
    "economy.middleware.DefaultLanguageMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "economy.middleware.FamilyTimezoneMiddleware",
    "economy.middleware.NetworkAccessMiddleware",
    "economy.middleware.AdminRateLimitMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kinkudos.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "economy.context_processors.family_context",
            ],
        },
    },
]

WSGI_APPLICATION = "kinkudos.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": Path(os.environ.get("KINKUDOS_DATABASE_PATH", BASE_DIR / "data" / "kinkudos.sqlite3")),
        "OPTIONS": {"timeout": 20},
    }
}

MEDIA_ROOT = Path(os.environ.get("KINKUDOS_MEDIA_ROOT", BASE_DIR / "data" / "media"))
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

LANGUAGE_CODE = os.environ.get("KINKUDOS_DEFAULT_LANGUAGE", "en")
LANGUAGES = [
    ("en", _("English")),
    ("lt", _("Lithuanian")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Vilnius"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "parent_login"
LOGIN_REDIRECT_URL = "parent_dashboard"
LOGOUT_REDIRECT_URL = "home"

SESSION_COOKIE_NAME = "kinkudos_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env_bool("KINKUDOS_SECURE_COOKIES", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("KINKUDOS_SECURE_COOKIES", not DEBUG)
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

PARENT_SESSION_SECONDS = int(os.environ.get("KINKUDOS_PARENT_SESSION_SECONDS", "86400"))
CHILD_SESSION_SECONDS = int(os.environ.get("KINKUDOS_CHILD_SESSION_SECONDS", "172800"))
PASSWORD_RESET_TIMEOUT = int(os.environ.get("KINKUDOS_PASSWORD_RESET_TIMEOUT", "3600"))
DEVICE_COOKIE_NAME = "kk_device"
DEVICE_PAIRING_REQUIRED = env_bool("KINKUDOS_DEVICE_PAIRING_REQUIRED", not DEBUG)
DEVICE_COOKIE_MAX_AGE = int(
    os.environ.get("KINKUDOS_DEVICE_COOKIE_MAX_AGE", str(365 * 24 * 60 * 60))
)
TRUSTED_PROXY_NETWORKS = env_list(
    "KINKUDOS_TRUSTED_PROXIES",
    "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
)
CLIENT_IP_HEADER = os.environ.get(
    "KINKUDOS_CLIENT_IP_HEADER",
    "HTTP_X_FORWARDED_FOR",
)
DJANGO_ADMIN_ENABLED = env_bool("KINKUDOS_DJANGO_ADMIN_ENABLED", False)
SETUP_TOKEN = secret_value("KINKUDOS_SETUP_TOKEN")

EMAIL_ENABLED = env_bool("KINKUDOS_EMAIL_ENABLED", False)
EMAIL_BACKEND = "economy.email_backend.EmailBackend"
EMAIL_HOST = os.environ.get("KINKUDOS_EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("KINKUDOS_EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("KINKUDOS_EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("KINKUDOS_EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.environ.get("KINKUDOS_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = secret_value("KINKUDOS_EMAIL_HOST_PASSWORD")
EMAIL_TIMEOUT = int(os.environ.get("KINKUDOS_EMAIL_TIMEOUT", "10"))
DEFAULT_FROM_EMAIL = os.environ.get(
    "KINKUDOS_DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER or "KinKudos <noreply@example.invalid>",
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
FEEDBACK_EMAIL = os.environ.get("KINKUDOS_FEEDBACK_EMAIL", "").strip()
SMTP_CONFIG_PATH = os.environ.get(
    "KINKUDOS_SMTP_CONFIG_PATH",
    str(BASE_DIR / "secrets" / "smtp" / "settings.json"),
)
BACKUP_AGENT_URL = os.environ.get("KINKUDOS_BACKUP_AGENT_URL", "").strip()
BACKUP_AGENT_TOKEN = secret_value("KINKUDOS_BACKUP_AGENT_TOKEN")

VAPID_PRIVATE_KEY = os.environ.get("KINKUDOS_VAPID_PRIVATE_KEY_FILE") or os.environ.get(
    "KINKUDOS_VAPID_PRIVATE_KEY",
    "",
)
VAPID_PUBLIC_KEY = secret_value("KINKUDOS_VAPID_PUBLIC_KEY")
VAPID_SUBJECT = os.environ.get("KINKUDOS_VAPID_SUBJECT", "mailto:admin@example.invalid")

SECURE_SSL_REDIRECT = env_bool("KINKUDOS_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("KINKUDOS_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("KINKUDOS_LOG_LEVEL", "INFO")},
}
