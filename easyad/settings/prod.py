import os

import dj_database_url
from dotenv import find_dotenv, load_dotenv

from .common import *

# Force python-dotenv to find the file and override any empty terminal variables
load_dotenv(find_dotenv(), override=True)
# --- CORE SETTINGS ---
# Safely convert DEBUG string to boolean, defaulting to False
# DEBUG = True
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "t")

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-default-change-me-in-production"
)

# Defaulting split strings to empty lists or local defaults to avoid crashes
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost 127.0.0.1").split(" ")

DJANGO_SETTINGS_MODULE = os.environ.get(
    "DJANGO_SETTINGS_MODULE", "myproject.settings.local"
)

# --- DATABASE ---
# Falls back to an in-memory SQLite database if no URL is provided
DEFAULT_DB_URL = "sqlite:///:memory:"
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    )
}

# --- AWS S3 STORAGE ---
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "default_aws_key")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "default_aws_secret")
AWS_STORAGE_BUCKET_NAME = os.environ.get(
    "AWS_STORAGE_BUCKET_NAME", "default-bucket-name"
)
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

# --- EXTERNAL API (TEXT EXPERT) ---
TEXT_EXPERT_USERNAME = os.environ.get("TEXT_EXPERT_USERNAME", "default_user")
TEXT_EXPERT_PASSWORD = os.environ.get("TEXT_EXPERT_PASSWORD", "default_password")
TEXT_EXPERT_API_KEY = os.environ.get("TEXT_EXPERT_API_KEY", "default_api_key")

# --- SECURITY & COOKIES ---
CORS_ALLOW_ALL_ORIGINS = True
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "http://localhost:8000 http://127.0.0.1:8000"
).split(" ")

CACHES["default"]["LOCATION"] = os.environ.get("REDIS_URL", "redis://localhost:6379")
