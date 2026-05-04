import pytest
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
