
import os

import dj_database_url

from .common import *

# --- CORE SETTINGS ---
DEBUG = False
ALLOWED_HOSTS = os.environ["ALLOWED_HOSTS"].split(" ") 
DJANGO_SETTINGS_MODULE = os.environ["DJANGO_SETTINGS_MODULE"]
SECRET_KEY = os.environ["SECRET_KEY"]


# --- DATABASE ---
DATABASES = {"default": dj_database_url.config()}

# --- EMAIL SETTINGS ---
DOMAIN = os.environ["WEBSITE_FRONT"]
WEBSITE = DOMAIN
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.environ["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = os.environ["EMAIL_HOST_PASSWORD"]
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# --- AWS S3 STORAGE ---
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

# --- EXTERNAL API (TEXT EXPERT) ---
TEXT_EXPERT_USERNAME = os.environ["TEXT_EXPERT_USERNAME"]
TEXT_EXPERT_PASSWORD = os.environ["TEXT_EXPERT_PASSWORD"]
TEXT_EXPERT_API_KEY = os.environ["TEXT_EXPERT_API_KEY"]


# --- SECURITY UTILITIES ---
def get_env_list(var_name, default=""):
    """Safely extracts a clean list of origins from environment variables."""
    value = os.environ.get(var_name, default)
    return [origin.strip() for origin in value.split(",") if origin.strip()]

# --- CORS CONFIGURATION ---
CORS_ALLOW_ALL_ORIGINS = False

# Load base production origins dynamically from environment variables
CORS_ALLOWED_ORIGINS = get_env_list(
    "CORS_ALLOWED_ORIGINS",
    default=(
        "https://feladoxi.com,"
        "https://www.feladoxi.com"
    )
)

# Regex matching for dynamic subdomains
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.feladoxi\.com$",
]

# --- CSRF & COOKIE SECURITY ---
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True       # Enforces HTTPS for session cookies
CSRF_COOKIE_HTTPONLY = True       # Prevents client-side JS from reading CSRF cookie

# Explicitly declare all exact origins and wildcard subdomains
CSRF_TRUSTED_ORIGINS = list(CORS_ALLOWED_ORIGINS) + [
    "https://*.feladoxi.com",
]
