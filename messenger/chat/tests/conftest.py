import pytest
from django.conf import settings


# Отключаем ATOMIC_REQUESTS для всех тестов
@pytest.fixture(scope="session", autouse=True)
def disable_atomic_requests(django_db_setup):
    settings.DATABASES['default']['ATOMIC_REQUESTS'] = False