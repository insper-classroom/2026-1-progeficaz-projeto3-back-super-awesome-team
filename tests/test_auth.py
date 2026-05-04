from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit


def get_query_params(location):
    return parse_qs(urlsplit(location).query)


@patch("app.routes.auth.login_service")
def test_login_ok(mock_service, client):
    mock_service.return_value = ({"token": "abc123"}, None)
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"token": "abc123"}


@patch("app.routes.auth.login_service")
def test_login_invalid_credentials(mock_service, client):
    mock_service.return_value = (None, {"error": "Credenciais inválidas"})
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Credenciais inválidas"}


@patch("app.routes.auth.login_service")
def test_login_unverified_email(mock_service, client):
    mock_service.return_value = (None, {"error": "E-mail ainda não verificado"})
    response = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "secret123"}
    )
    assert response.status_code == 403
    assert response.get_json() == {"error": "E-mail ainda não verificado"}


@patch("app.routes.auth.verify_email_service")
def test_verify_email_ok(mock_service, client):
    mock_service.return_value = ({"message": "E-mail confirmado com sucesso"}, None)
    response = client.get("/auth/verify-email/valid-token")
    assert response.status_code == 200
    assert response.get_json() == {"message": "E-mail confirmado com sucesso"}


@patch("app.routes.auth.verify_email_service")
def test_verify_email_invalid_token(mock_service, client):
    mock_service.return_value = (None, {"error": "Token inválido ou expirado"})
    response = client.get("/auth/verify-email/bad-token")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Token inválido ou expirado"}


@patch("app.routes.auth.verify_email_service")
def test_verify_email_ok_redirects_to_frontend(mock_service, client, monkeypatch):
    monkeypatch.setenv(
        "FRONTEND_EMAIL_VERIFIED_URL", "http://localhost:5173/email-verified"
    )
    mock_service.return_value = ({"message": "E-mail confirmado com sucesso"}, None)

    response = client.get("/auth/verify-email/valid-token")

    assert response.status_code == 302
    assert urlsplit(response.location).path == "/email-verified"
    assert get_query_params(response.location) == {
        "status": ["success"],
        "message": ["E-mail confirmado com sucesso"],
    }


@patch("app.routes.auth.verify_email_service")
def test_verify_email_invalid_token_redirects_to_frontend(
    mock_service, client, monkeypatch
):
    monkeypatch.setenv(
        "FRONTEND_EMAIL_VERIFIED_URL", "http://localhost:5173/email-verified"
    )
    mock_service.return_value = (None, {"error": "Token inválido ou expirado"})

    response = client.get("/auth/verify-email/bad-token")

    assert response.status_code == 302
    assert urlsplit(response.location).path == "/email-verified"
    assert get_query_params(response.location) == {
        "status": ["error"],
        "message": ["Token inválido ou expirado"],
    }


@patch("app.routes.auth.request_password_reset_service")
def test_forgot_password_ok(mock_service, client):
    mock_service.return_value = (
        {"message": "Se o e-mail existir, o código será enviado"},
        None,
    )
    response = client.post(
        "/auth/forgot-password", json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Se o e-mail existir, o código será enviado"
    }


@patch("app.routes.auth.request_password_reset_service")
def test_forgot_password_error(mock_service, client):
    mock_service.return_value = (None, {"error": "Erro inesperado"})
    response = client.post("/auth/forgot-password", json={})
    assert response.status_code == 400


@patch("app.routes.auth.verify_reset_code_service")
def test_verify_reset_code_ok(mock_service, client):
    mock_service.return_value = ({"reset_token": "some-uuid"}, None)
    response = client.post(
        "/auth/verify-reset-code",
        json={"email": "test@example.com", "code": "123456"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"reset_token": "some-uuid"}


@patch("app.routes.auth.verify_reset_code_service")
def test_verify_reset_code_invalid(mock_service, client):
    mock_service.return_value = (None, {"error": "Código inválido ou expirado"})
    response = client.post(
        "/auth/verify-reset-code",
        json={"email": "test@example.com", "code": "000000"},
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "Código inválido ou expirado"}


@patch("app.routes.auth.reset_password_service")
def test_reset_password_ok(mock_service, client):
    mock_service.return_value = ({"message": "Senha alterada com sucesso"}, None)
    response = client.post(
        "/auth/reset-password",
        json={"reset_token": "some-uuid", "new_password": "newpass123"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Senha alterada com sucesso"}


@patch("app.routes.auth.reset_password_service")
def test_reset_password_missing_fields(mock_service, client):
    mock_service.return_value = (
        None,
        {"error": "reset_token e new_password são obrigatórios"},
    )
    response = client.post("/auth/reset-password", json={})
    assert response.status_code == 400
    assert response.get_json() == {
        "error": "reset_token e new_password são obrigatórios"
    }
