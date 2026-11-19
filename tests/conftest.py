import pytest

from app import app as flask_app


@pytest.fixture
def client():
    """Тестовый клиент Flask: отправляет запросы к приложению без браузера."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client