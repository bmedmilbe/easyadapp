import pytest


@pytest.fixture(autouse=True)
def use_dummy_storage(settings):
    """
    Overrides the default storage backends during test execution.
    - Redirects media uploads (user files) to an isolated memory buffer to prevent S3 API calls.
    - Correctly configures static files using Django's core contrib namespace to satisfy WhiteNoise.
    """
    settings.STORAGES = {
        # Keeps user-uploaded media files in-memory during testing
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        # Correct path for static files (CSS/JS) required by Django and WhiteNoise
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
    # Backwards compatibility flags for legacy setups
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
