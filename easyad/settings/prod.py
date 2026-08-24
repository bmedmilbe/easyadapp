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
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com" 

# --- EXTERNAL API (TEXT EXPERT) ---
TEXT_EXPERT_USERNAME = os.environ["TEXT_EXPERT_USERNAME"]
TEXT_EXPERT_PASSWORD = os.environ["TEXT_EXPERT_PASSWORD"]
TEXT_EXPERT_API_KEY = os.environ["TEXT_EXPERT_API_KEY"]

# --- SECURITY UTILITIES ---
def get_env_list(var_name, default=""):
    """Extracts a clean list of origins from environment variables."""
    value = os.environ.get(var_name, default)
    if isinstance(value, list) or isinstance(value, tuple):
        return list(value)
    return [origin.strip() for origin in value.split(",") if origin.strip()]

# --- GLOBAL CORS RULES ---
# Allows developers to query this live API via javascript from localhost
CORS_ALLOW_ALL_ORIGINS = True

# --- CSRF & COOKIE SECURITY FOR LIVE ADMIN ---
# Keeps the admin panel secure over HTTPS while allowing trusted cross-origin interaction
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Explicitly trust the production domain (for admin login) and local web servers
CSRF_TRUSTED_ORIGINS = [
    "https://easyadapp-production.up.railway.app",  # Your admin panel URL
    "http://localhost:3000",                        # Local React/Vite development apps
    "http://127.0.0.1:3000",                       # Local host IP fallbacks
    "http://localhost:5173",                        # Common fallback Vite server port
] + get_env_list("CORS_ALLOWED_ORIGINS", default=[])
