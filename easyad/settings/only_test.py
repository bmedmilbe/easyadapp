

from .dev import *

CACHES={
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DEFAULT_FILE_STORAGE = "inmemorystorage.InMemoryStorage"

CACHES["default"]["BACKEND"] = "django.core.cache.backends.locmem.LocMemCache"

WHITENOISE_AUTOREFRESH = True

DATABASE_URL = 'postgresql://postgres:postgres@host.docker.internal:5432/easyaddbtest'

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL) 
}
DATABASES["default"]["TEST"] = {"SERIALIZE": False}





