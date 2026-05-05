from unittest.mock import patch

GOAL_ID = "507f1f77bcf86cd799439011"
GROUP_ID = "507f1f77bcf86cd799439012"
USER_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"

GOAL_DATA = {
    "_id": GOAL_ID,
    "name": "Meta teste",
    "group_id": GROUP_ID,
    "members": [USER_EMAIL, OTHER_EMAIL],
    "current_value": 130.0,
    "contributions": [
        {
            "member_email": USER_EMAIL,
            "value": 40.0,
            "contributed_at": "2026-05-01T12:00:00Z",
        },
        {
            "member_email": OTHER_EMAIL,
            "value": 90.0,
            "contributed_at": "2026-05-03T12:00:00Z",
        },
    ],
}

GOAL_PAYLOAD = {
    "name": "Meta teste",
    "target_value": 500.0,
    "group_id": GROUP_ID,
}


def test_create_goal_no_token(client):
    response = client.post("/goal", json=GOAL_PAYLOAD)
    assert response.status_code == 401


@patch("app.routes.goal.create_goal_service")
def test_create_goal_ok(mock_service, client, auth_headers):
    mock_service.return_value = (
        {"message": "Meta criada com sucesso", "goal_id": GOAL_ID},
        None,
    )
    response = client.post("/goal", json=GOAL_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()["goal_id"] == GOAL_ID


@patch("app.routes.goal.create_goal_service")
def test_create_goal_validation_error(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"name": ["Missing data for required field."]})
    response = client.post("/goal", json={}, headers=auth_headers)
    assert response.status_code == 400


@patch("app.routes.goal.create_goal_service")
def test_create_goal_group_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.post("/goal", json=GOAL_PAYLOAD, headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.goal.create_goal_service")
def test_create_goal_user_not_member(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Você não é membro deste grupo"})
    response = client.post("/goal", json=GOAL_PAYLOAD, headers=auth_headers)
    assert response.status_code == 403


def test_get_user_goals_no_token(client):
    response = client.get("/goal")
    assert response.status_code == 401


@patch("app.routes.goal.get_user_goals_service")
def test_get_user_goals_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([GOAL_DATA], None)
    response = client.get("/goal", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "goals" in data
    assert len(data["goals"]) == 1


@patch("app.routes.goal.get_user_goals_service")
def test_get_user_goals_empty(mock_service, client, auth_headers):
    mock_service.return_value = ([], None)
    response = client.get("/goal", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json() == {"goals": []}


def test_get_group_goals_no_token(client):
    response = client.get(f"/group/{GROUP_ID}/goal")
    assert response.status_code == 401


@patch("app.routes.goal.get_group_goals_service")
def test_get_group_goals_ok(mock_service, client, auth_headers):
    mock_service.return_value = ([GOAL_DATA], None)
    response = client.get(f"/group/{GROUP_ID}/goal", headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "goals" in data
    assert len(data["goals"]) == 1


@patch("app.routes.goal.get_group_goals_service")
def test_get_group_goals_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Grupo não encontrado"})
    response = client.get(f"/group/{GROUP_ID}/goal", headers=auth_headers)
    assert response.status_code == 404


@patch("app.routes.goal.get_group_goals_service")
def test_get_group_goals_forbidden(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Você não é membro deste grupo"})
    response = client.get(f"/group/{GROUP_ID}/goal", headers=auth_headers)
    assert response.status_code == 403


def test_get_goal_no_token(client):
    response = client.get(f"/goal/{GOAL_ID}")
    assert response.status_code == 401


@patch("app.routes.goal.get_goal_service")
def test_get_goal_ok(mock_service, client, auth_headers):
    mock_service.return_value = (GOAL_DATA, None)
    response = client.get(f"/goal/{GOAL_ID}", headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()["_id"] == GOAL_ID


@patch("app.routes.goal.get_goal_service")
def test_get_goal_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Meta não encontrada"})
    response = client.get(f"/goal/{GOAL_ID}", headers=auth_headers)
    assert response.status_code == 404


def test_update_goal_no_token(client):
    response = client.put(f"/goal/{GOAL_ID}", json={"name": "Nova meta"})
    assert response.status_code == 401


@patch("app.routes.goal.update_goal_service")
def test_update_goal_ok(mock_service, client, auth_headers):
    updated = {**GOAL_DATA, "name": "Meta atualizada"}
    mock_service.return_value = (
        {"message": "Meta atualizada com sucesso", "goal": updated},
        None,
    )
    response = client.put(
        f"/goal/{GOAL_ID}", json={"name": "Meta atualizada"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.get_json()["message"] == "Meta atualizada com sucesso"


@patch("app.routes.goal.update_goal_service")
def test_update_goal_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Meta não encontrada"})
    response = client.put(
        f"/goal/{GOAL_ID}", json={"name": "X"}, headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_goal_no_token(client):
    response = client.delete(f"/goal/{GOAL_ID}")
    assert response.status_code == 401


@patch("app.routes.goal.delete_goal_service")
def test_delete_goal_ok(mock_service, client, auth_headers):
    mock_service.return_value = ({"message": "Meta deletada com sucesso"}, None)
    response = client.delete(f"/goal/{GOAL_ID}", headers=auth_headers)
    assert response.status_code == 204
    assert response.data == b""


@patch("app.routes.goal.delete_goal_service")
def test_delete_goal_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Meta não encontrada"})
    response = client.delete(f"/goal/{GOAL_ID}", headers=auth_headers)
    assert response.status_code == 404


def test_add_goal_contribution_no_token(client):
    response = client.post(f"/goal/{GOAL_ID}/contribution", json={"value": 50.0})
    assert response.status_code == 401


@patch("app.routes.goal.add_goal_contribution_service")
def test_add_goal_contribution_ok(mock_service, client, auth_headers):
    updated = {**GOAL_DATA, "current_value": 180.0}
    mock_service.return_value = (
        {"message": "Aporte registrado com sucesso", "goal": updated},
        None,
    )
    response = client.post(
        f"/goal/{GOAL_ID}/contribution",
        json={"value": 50.0},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.get_json()["message"] == "Aporte registrado com sucesso"


@patch("app.routes.goal.add_goal_contribution_service")
def test_add_goal_contribution_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Meta não encontrada"})
    response = client.post(
        f"/goal/{GOAL_ID}/contribution",
        json={"value": 50.0},
        headers=auth_headers,
    )
    assert response.status_code == 404


@patch("app.routes.goal.add_goal_contribution_service")
def test_add_goal_contribution_validation_error(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"value": ["Missing data for required field."]})
    response = client.post(
        f"/goal/{GOAL_ID}/contribution",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_update_goal_contribution_no_token(client):
    response = client.put(f"/goal/{GOAL_ID}/contribution/1", json={"value": 90.0})

    assert response.status_code == 401


@patch("app.routes.goal.update_goal_contribution_service")
def test_update_goal_contribution_ok(mock_service, client, auth_headers):
    payload = {
        "value": 90.0,
        "member_email": OTHER_EMAIL,
        "contributed_at": "2026-05-03T12:00:00Z",
    }
    mock_service.return_value = (
        {"message": "Aporte atualizado com sucesso", "goal": GOAL_DATA},
        None,
    )

    response = client.put(
        f"/goal/{GOAL_ID}/contribution/1", json=payload, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.get_json()["goal"]["current_value"] == 130.0
    mock_service.assert_called_once_with(GOAL_ID, 1, payload, USER_EMAIL)


@patch("app.routes.goal.update_goal_contribution_service")
def test_update_goal_contribution_not_found(mock_service, client, auth_headers):
    mock_service.return_value = (None, {"error": "Aporte não encontrado"})

    response = client.put(
        f"/goal/{GOAL_ID}/contribution/99",
        json={"value": 90.0},
        headers=auth_headers,
    )

    assert response.status_code == 404
