from unittest.mock import patch

USER_PAYLOAD = {
    "name": "Test User",
    "email": "test@example.com",
    "password": "secret123",
    "confirm_password": "secret123",
}


@patch("app.routes.user.create_user_service")
def test_create_user_ok(mock_service, client):
    mock_service.return_value = ({"message": "OK ✅"}, None)
    response = client.post("/user", json=USER_PAYLOAD)
    assert response.status_code == 201
    assert response.get_json() == {"message": "OK ✅"}


@patch("app.routes.user.create_user_service")
def test_create_user_email_exists(mock_service, client):
    mock_service.return_value = (None, {"error": "email já cadastrado"})
    response = client.post("/user", json=USER_PAYLOAD)
    assert response.status_code == 409
    assert response.get_json() == {"error": "email já cadastrado"}


@patch("app.routes.user.create_user_service")
def test_create_user_validation_error(mock_service, client):
    mock_service.return_value = (None, {"email": ["Not a valid email address."]})
    response = client.post(
        "/user",
        json={"name": "Test", "email": "not-an-email", "password": "123456"},
    )
    assert response.status_code == 400


def test_get_current_user_no_token(client):
    response = client.get("/user/me")
    assert response.status_code == 401


@patch("app.routes.user.get_current_user_service")
def test_get_current_user_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"_id": "abc", "name": "Test User", "email": "test@example.com"},
        None,
    )
    response = client.get("/user/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["email"] == "test@example.com"


@patch("app.routes.user.get_current_user_service")
def test_get_current_user_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Usuário não encontrado"})
    response = client.get("/user/me", headers=auth_headers)
    assert response.status_code == 404


def test_update_user_no_token(client):
    response = client.put("/user/me", json={"name": "New Name"})
    assert response.status_code == 401


@patch("app.routes.user.update_user_service")
def test_update_user_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Usuário atualizado com sucesso"}, None)
    response = client.put("/user/me", json={"name": "New Name"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {"message": "Usuário atualizado com sucesso"}


@patch("app.routes.user.update_user_service")
def test_update_user_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Usuário não encontrado"})
    response = client.put("/user/me", json={"name": "New Name"}, headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.user.update_user_service")
def test_update_user_no_fields_changed(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Nenhum campo alterado"})
    response = client.put("/user/me", json={}, headers=auth_headers)
    assert response.status_code == 400


@patch("app.routes.user.update_user_service")
def test_update_user_wrong_current_password(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Senha atual incorreta"})
    response = client.put(
        "/user/me",
        json={"password": "newpass123", "current_password": "wrong"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_delete_user_no_token(client):
    response = client.delete("/user/me")
    assert response.status_code == 401


@patch("app.routes.user.delete_user_service")
def test_delete_user_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Usuário deletado com sucesso"}, None)
    response = client.delete(
        "/user/me", json={"password": "secret123"}, headers=auth_headers
    )
    assert response.status_code == 204
    assert response.data == b""


@patch("app.routes.user.delete_user_service")
def test_delete_user_wrong_password(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Senha incorreta"})
    response = client.delete(
        "/user/me", json={"password": "wrong"}, headers=auth_headers
    )
    assert response.status_code == 400


@patch("app.routes.user.create_user_service")
def test_create_user_with_image_ok(mock_service, client):
    mock_service.return_value = ({"message": "OK ✅"}, None)
    response = client.post(
        "/user",
        json={**USER_PAYLOAD, "image": "https://example.com/photo.jpg"},
    )
    assert response.status_code == 201
    assert response.get_json() == {"message": "OK ✅"}


@patch("app.routes.user.update_user_service")
def test_update_user_image_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Usuário atualizado com sucesso"}, None)
    response = client.put(
        "/user/me",
        json={"image": "https://example.com/new-photo.jpg"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Usuário atualizado com sucesso"}


@patch("app.routes.user.delete_user_service")
def test_delete_user_has_groups(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {
            "error": "Não é possível excluir a conta: você criou grupos. Exclua ou transfira esses grupos antes."
        },
    )
    response = client.delete(
        "/user/me", json={"password": "secret123"}, headers=auth_headers
    )
    assert response.status_code == 409
