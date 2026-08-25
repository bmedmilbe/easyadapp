import pytest


@pytest.fixture(autouse=True)
def use_dummy_storage(settings):
    """
    Substitui o armazenamento da S3 por armazenamento em memória 
    automaticamente para todos os testes do projeto.
    """
    # Para Django >= 4.2
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {"BACKEND": "django.core.files.storage.StaticFilesStorage"},
    }
    # Para garantir compatibilidade com versões anteriores se ainda usado:
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"
