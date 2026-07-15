
from .common import *

# --- CORE SETTINGS ---
DEBUG = False
ALLOWED_HOSTS = ["tendastpapp-2de898e9780e.herokuapp.com"]
DJANGO_SETTINGS_MODULE = os.environ["DJANGO_SETTINGS_MODULE"]
SECRET_KEY = os.environ["SECRET_KEY"]

# --- CORS CONFIGURATION ---
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://felaglandji.com",
    "https://contaviva.vercel.app",
    "https://ladyfish.vercel.app",
    "https://www.contachiquila.com",
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.felaglandji\.com$",
    r"^https://\w+\.contachiquila\.com$",
]

# --- CSRF & SECURITY ---
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS + [
    "https://*.felaglandji.com",
    "https://*.contachiquila.com",
]

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