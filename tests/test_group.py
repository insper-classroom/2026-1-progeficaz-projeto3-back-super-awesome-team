from unittest.mock import patch

GROUP_ID = "507f1f77bcf86cd799439011"

GROUP_DATA = {
    "_id": GROUP_ID,
    "name": "My Group",
    "members": ["test@example.com"],
    "created_by": "test@example.com",
}


def test_create_group_no_token(client):
    response = client.post("/group", json={"name": "My Group"})
    assert response.status_code == 401


@patch("app.routes.group.create_group_service")
def test_create_group_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Grupo criado com sucesso", "group_id": GROUP_ID},
        None,
    )
    response = client.post(
        "/group",
        json={"name": "My Group", "members": ["test@example.com"]},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.get_json()["group_id"] == GROUP_ID


@patch("app.routes.group.create_group_service")
def test_create_group_validation_error(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"name": ["Missing data for required field."]})
    response = client.post("/group", json={}, headers=auth_headers)
    assert response.status_code == 400


@patch("app.routes.group.create_group_service")
def test_create_group_member_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Usuário other@example.com não encontrado"},
    )
    response = client.post(
        "/group",
        json={"name": "My Group", "members": ["other@example.com"]},
        headers=auth_headers,
    )
    assert response.status_code == 404


@patch("app.routes.group.create_group_service")
def test_create_group_with_image_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Grupo criado com sucesso", "group_id": GROUP_ID},
        None,
    )
    response = client.post(
        "/group",
        json={
            "name": "My Group",
            "members": ["test@example.com"],
            "image": "https://example.com/group.jpg",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.get_json()["group_id"] == GROUP_ID


@patch("app.routes.group.update_group_service")
def test_update_group_image_ok(mock_service, client, auth_headers):
    updated = {**GROUP_DATA, "image": "https://example.com/new-group.jpg"}
    mock_service.return_value = (
        {"message": "Grupo atualizado com sucesso", "group": updated},
        None,
    )
    response = client.put(
        f"/group/{GROUP_ID}",
        json={"image": "https://example.com/new-group.jpg"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Grupo atualizado com sucesso"


def test_get_user_groups_no_token(client):
    response = client.get("/group")
    assert response.status_code == 401


@patch("app.routes.group.get_user_groups_service")
def test_get_user_groups_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([GROUP_DATA], None)
    response = client.get("/group", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "groups" in data
    assert len(data["groups"]) == 1


@patch("app.routes.group.get_group_service")
def test_get_group_ok(mock_service, client, auth_headers):
    mock_service.return_value = (GROUP_DATA, None)
    response = client.get(f"/group/{GROUP_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["_id"] == GROUP_ID


@patch("app.routes.group.get_group_service")
def test_get_group_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.get(f"/group/{GROUP_ID}", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.group.get_group_service")
def test_get_group_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Você não é membro deste grupo"})
    response = client.get(f"/group/{GROUP_ID}", headers=auth_headers)
    assert response.status_code == 403


@patch("app.routes.group.update_group_service")
def test_update_group_ok(mock_service, client, auth_headers):
    updated = {**GROUP_DATA, "name": "Updated Group"}
    mock_service.return_value = (
        {"message": "Grupo atualizado com sucesso", "group": updated},
        None,
    )
    response = client.put(
        f"/group/{GROUP_ID}", json={"name": "Updated Group"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Grupo atualizado com sucesso"


@patch("app.routes.group.update_group_service")
def test_update_group_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.put(
        f"/group/{GROUP_ID}", json={"name": "X"}, headers=auth_headers
    )
    assert response.status_code == 404


@patch("app.routes.group.update_group_service")
def test_update_group_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Você não é membro deste grupo"})
    response = client.put(
        f"/group/{GROUP_ID}", json={"name": "X"}, headers=auth_headers
    )
    assert response.status_code == 403


def test_delete_group_no_token(client):
    response = client.delete(f"/group/{GROUP_ID}")
    assert response.status_code == 401


@patch("app.routes.group.delete_group_service")
def test_delete_group_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Grupo e seus dados associados foram deletados com sucesso"},
        None,
    )
    response = client.delete(f"/group/{GROUP_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Grupo e seus dados associados foram deletados com sucesso"
    }


@patch("app.routes.group.delete_group_service")
def test_delete_group_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (
        None,
        {"error": "Apenas o criador do grupo pode deletá-lo"},
    )
    response = client.delete(f"/group/{GROUP_ID}", headers=auth_headers)
    assert response.status_code == 403
