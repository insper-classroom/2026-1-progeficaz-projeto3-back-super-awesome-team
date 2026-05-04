import pytest
import os

os.environ.update(
    {
        "FRONTEND_AUTH_CALLBACK_URL": "",
        "FRONTEND_EMAIL_VERIFIED_URL": "",
        "FRONTEND_URL": "",
        "JWT_SECRET_KEY": "test-jwt-secret-key-with-at-least-32-bytes",
        "MONGODB_URI": "mongodb://localhost:27017",
        "SECRET_KEY": "test-secret-key",
    }
)

from app import create_app
from app.utils.jwt_utils import generate_token

TEST_EMAIL = "test@example.com"


@pytest.fixture
def app():
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_headers():
    token = generate_token(TEST_EMAIL)
    return {"Authorization": f"Bearer {token}"}
